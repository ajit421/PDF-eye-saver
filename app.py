import streamlit as st
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader
import io  # <--- Essential for fixing file corruption

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
    Fixes:
    1. Removes spaces from filenames to prevent broken links.
    2. Uses io.BytesIO to prevent file corruption.
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
            # --- FIX 1: Make Filename Safe ---
            # Replace spaces with underscores and remove double extension
            safe_name = file_name.replace(" ", "_").replace(".pdf", "")
            
            # --- FIX 2: Convert to Stream ---
            # Cloudinary needs a 'file-like object', not raw bytes
            file_stream = io.BytesIO(file_bytes)
            
            # 3. Upload command
            # resource_type="auto" detects if it is a PDF or Image automatically
            response = cloudinary.uploader.upload(file_stream, resource_type="auto", public_id=safe_name)
            
            # 4. Return the Secure Public URL
            return response.get("secure_url")
            
        except Exception as e:
            st.error(f"Cloudinary Connection Error: {e}")
            return None
    else:
        # If running locally without secrets, skip upload silently
        return None

def change_pdf_background(file_bytes, color_hex, intensity=0.3, is_overlay=False):
    """
    Core Logic: Changes the background of the PDF.
    """
    # Open the PDF from memory
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    rgb_color = hex_to_rgb(color_hex)

    for page in doc:
        rect = page.rect
        shape = page.new_shape()
        
        if is_overlay:
            # Overlay Mode: Draws a transparent layer ON TOP of text
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, fill_opacity=intensity, color=None) 
            shape.commit(overlay=True)
        else:
            # Standard Mode: Draws a solid layer BEHIND text
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, color=rgb_color)
            shape.commit(overlay=False)

    return doc

# --- Streamlit UI Code ---

st.set_page_config(page_title="PDF Eye-Saver", page_icon="📄", layout="wide")

st.title("📄 PDF Eye-Saver & Background Changer")
st.markdown(""" 
Make your PDFs easier to read! 
* **Standard Mode:** Puts color *behind* the text (Best for digital PDFs).
* **Overlay Mode:** Puts a transparent color *on top* (Best for scanned papers/images).
""")

# Layout: Split screen into two columns
col1, col2 = st.columns([1, 1])

# --- LEFT COLUMN: Inputs & Processing ---
with col1:
    st.subheader("1. Upload & Settings")
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

    # Color Picker
    color_hex = st.color_picker("Pick a Background Color", "#FFFFCC") 
    
    # Overlay Mode Toggle
    is_overlay = st.checkbox("Enable Overlay Mode (For Scanned PDFs)", value=False)
    
    # Intensity Slider (Only shows if Overlay is checked)
    intensity = 0.3
    if is_overlay:
        st.info("ℹ️ Overlay mode adds a 'tint' on top of the page.")
        intensity = st.slider("Tint Intensity (Darkness)", 0.1, 0.9, 0.3)

    # The Big Button
    process_btn = st.button("Process PDF", type="primary")

    # --- MAIN LOGIC ---
    if process_btn and uploaded_file is not None:
        # Read file safely
        file_bytes = uploaded_file.getvalue()
        
        with st.spinner("Processing & Backing up to Cloud..."):
            
            # 1. Cloudinary Backup (Runs in background)
            file_url = upload_to_cloudinary(file_bytes, uploaded_file.name)
            
            if file_url:
                st.toast("✅ File saved to Cloud storage!", icon="☁️")
                # Show the link to the user
                st.markdown(f"**Backup Link:** [View on Cloud]({file_url})")
            
            try:
                # 2. PDF Processing (The main job)
                modified_doc = change_pdf_background(file_bytes, color_hex, intensity, is_overlay)
                modified_pdf_bytes = modified_doc.tobytes()
                
                # Close doc to free memory
                modified_doc.close()
                
                # 3. Success!
                st.balloons()
                st.success("Processing Complete!")
                
                # 4. Download Button (Appears right here)
                new_name = f"colored_{uploaded_file.name}"
                
                st.download_button(
                    label="📥 Download Modified PDF",
                    data=modified_pdf_bytes,
                    file_name=new_name,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- RIGHT COLUMN: Preview ---
with col2:
    if uploaded_file is not None:
        st.subheader("2. Preview")
        
        # We read the file bytes again for the preview
        file_bytes = uploaded_file.getvalue()
        
        try:
            # Open a temporary doc just for preview
            preview_doc = fitz.open(stream=file_bytes, filetype="pdf")
            first_page = preview_doc[0]
            
            # Apply the effect to the first page only
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
            
            # Convert to image for Streamlit display
            pix = first_page.get_pixmap(dpi=100)
            st.image(pix.tobytes(), caption="Preview of Page 1", use_container_width=True)
            
            preview_doc.close()
            
        except Exception as e:
            st.error(f"Error generating preview: {e}")