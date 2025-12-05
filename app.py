import streamlit as st
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader
import io  

# --- Helper Functions ---

def hex_to_rgb(hex_color):
    """
    Converts hex color ('#RRGGBB') to a tuple (r, g, b) with values 0-1.
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def upload_to_cloudinary(file_bytes, file_name):
    """
    Uploads the file to Cloudinary securely.
    """
    # 1. Check if secrets exist
    if "cloudinary" in st.secrets:
        secret = st.secrets["cloudinary"]
        
        # 2. Configure Cloudinary
        cloudinary.config(
            cloud_name = secret["cloud_name"],
            api_key = secret["api_key"],
            api_secret = secret["api_secret"]
        )
        
        try:
            # Fix Filename & Stream
            safe_name = file_name.replace(" ", "_").replace(".pdf", "")
            file_stream = io.BytesIO(file_bytes)
            
            # Upload command
            response = cloudinary.uploader.upload(file_stream, resource_type="auto", public_id=safe_name)
            
            # Return URL
            return response.get("secure_url")
            
        except Exception as e:
            # Fail silently (don't show error to user if backup fails)
            print(f"Backup Error: {e}")
            return None
    else:
        return None

def change_pdf_background(file_bytes, color_hex, intensity=0.3, is_overlay=False):
    """
    Core Logic: Changes the background of the PDF.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    rgb_color = hex_to_rgb(color_hex)

    for page in doc:
        rect = page.rect
        shape = page.new_shape()
        
        if is_overlay:
            # Overlay Mode
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, fill_opacity=intensity, color=None) 
            shape.commit(overlay=True)
        else:
            # Standard Mode
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, color=rgb_color)
            shape.commit(overlay=False)

    return doc

# --- Streamlit UI Code ---

st.set_page_config(page_title="PDF Eye-Saver", page_icon="📄", layout="wide")

st.title("📄 PDF Eye-Saver & Background Changer")
st.markdown(""" 
Make your PDFs easier to read! 
* **Standard Mode:** Best for digital PDFs.
* **Overlay Mode:** Best for scanned papers/images.
""")

# Layout
col1, col2 = st.columns([1, 1])

# --- LEFT COLUMN ---
with col1:
    st.subheader("1. Upload & Settings")
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

    color_hex = st.color_picker("Pick a Background Color", "#FFFFCC") 
    
    is_overlay = st.checkbox("Enable Overlay Mode (For Scanned PDFs)", value=False)
    
    intensity = 0.3
    if is_overlay:
        st.info("ℹ️ Overlay mode adds a 'tint' on top of the page.")
        intensity = st.slider("Tint Intensity", 0.1, 0.9, 0.3)

    process_btn = st.button("Process PDF", type="primary")

    # --- MAIN LOGIC ---
    if process_btn and uploaded_file is not None:
        # Read file safely
        file_bytes = uploaded_file.getvalue()
        
        with st.spinner("Processing..."):
            upload_to_cloudinary(file_bytes, uploaded_file.name)
            
            try:
                # 2. PDF Processing
                modified_doc = change_pdf_background(file_bytes, color_hex, intensity, is_overlay)
                modified_pdf_bytes = modified_doc.tobytes()
                modified_doc.close()
                
                st.balloons()
                st.success("Processing Complete!")
                
                new_name = f"colored_{uploaded_file.name}"
                
                st.download_button(
                    label="📥 Download Modified PDF",
                    data=modified_pdf_bytes,
                    file_name=new_name,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- RIGHT COLUMN ---
with col2:
    if uploaded_file is not None:
        st.subheader("2. Preview")
        file_bytes = uploaded_file.getvalue()
        
        try:
            preview_doc = fitz.open(stream=file_bytes, filetype="pdf")
            first_page = preview_doc[0]
            
            # Apply effect
            rect = first_page.rect
            shape = first_page.new_shape()
            rgb_color = hex_to_rgb(color_hex)
            
            if is_overlay:
                shape.draw_rect(rect)
                shape.finish(fill=rgb_color, fill_opacity=intensity, color=None)
                shape.commit(overlay=True)
            else:
                shape.draw_rect(rect)
                shape.finish(fill=rgb_color, color=rgb_color)
                shape.commit(overlay=False)
            
            pix = first_page.get_pixmap(dpi=100)
            st.image(pix.tobytes(), caption="Preview of Page 1", use_container_width=True)
            preview_doc.close()
            
        except Exception as e:
            st.error(f"Preview Error: {e}")