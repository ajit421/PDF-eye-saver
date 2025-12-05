import streamlit as st
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader

# --- Helper Functions ---
def hex_to_rgb(hex_color):
    """Converts hex color ('#RRGGBB') to a tuple (r, g, b) with values 0-1."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def upload_to_cloudinary(file_bytes, file_name):
    """
    Uploads to Cloudinary with a SAFE filename (no spaces).
    """
    if "cloudinary" in st.secrets:
        secret = st.secrets["cloudinary"]
        
        cloudinary.config(
            cloud_name = secret["cloud_name"],
            api_key = secret["api_key"],
            api_secret = secret["api_secret"]
        )
        
        try:
            # --- NEW CODE: Make filename safe ---
            # 1. Replace spaces with underscores (_)
            # 2. Remove the extra .pdf if it exists to avoid .pdf.pdf
            safe_name = file_name.replace(" ", "_").replace(".pdf", "")
            
            # Upload with the clean name
            response = cloudinary.uploader.upload(file_bytes, resource_type="auto", public_id=safe_name)
            return response.get("secure_url")
            
        except Exception as e:
            st.error(f"Cloudinary Error: {e}")
            return None
    else:
        return None

def change_pdf_background(file_bytes, color_hex, intensity=0.3, is_overlay=False):
    """
    Changes the background of the PDF.
    - file_bytes: The raw PDF data.
    - color_hex: Color selected by user.
    - intensity: Opacity level for overlay mode.
    - is_overlay: If True, draws ON TOP of text (tint).
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    rgb_color = hex_to_rgb(color_hex)

    for page in doc:
        rect = page.rect
        shape = page.new_shape()
        
        if is_overlay:
            # Overlay Mode (Tint)
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, fill_opacity=intensity, color=None) 
            shape.commit(overlay=True)
        else:
            # Standard Mode (Background)
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

# Layout: Left for Settings, Right for Preview
col1, col2 = st.columns([1, 1])

# --- LEFT COLUMN (Inputs & Download Button) ---
with col1:
    st.subheader("1. Upload & Settings")
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

    # Pick a color
    color_hex = st.color_picker("Pick a Background Color", "#FFFFCC") 
    
    # Checkbox for Overlay
    is_overlay = st.checkbox("Enable Overlay Mode (For Scanned PDFs)", value=False)
    
    # Initialize intensity
    intensity = 0.3

    if is_overlay:
        st.info("ℹ️ Overlay mode adds a 'tint' on top of the page.")
        intensity = st.slider("Tint Intensity (Darkness)", 0.1, 0.9, 0.3)

    # Process Button
    process_btn = st.button("Process PDF", type="primary")

    # --- MAIN LOGIC (Running inside Col 1) ---
    if process_btn and uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        
        with st.spinner("Processing..."):
            
            # 1. Cloudinary Backup (Optional)
            file_url = upload_to_cloudinary(file_bytes, uploaded_file.name)
            if file_url:
                st.toast("✅ File saved to Cloud!", icon="☁️")
                # Showing link is optional, can be removed for privacy
                st.markdown(f"**Backup Link:** [View File]({file_url})")
            
            try:
                # 2. PDF Processing
                modified_doc = change_pdf_background(file_bytes, color_hex, intensity, is_overlay)
                modified_pdf_bytes = modified_doc.tobytes()
                modified_doc.close()
                
                # 3. Success & Download
                st.balloons()
                st.success("Processing Complete!")
                
                # Dynamic Filename
                original_name = uploaded_file.name
                new_name = f"colored_{original_name}"
                
                # Download Button
                st.download_button(
                    label="📥 Download Modified PDF",
                    data=modified_pdf_bytes,
                    file_name=new_name,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- RIGHT COLUMN (Preview Only) ---
with col2:
    if uploaded_file is not None:
        st.subheader("2. Preview")
        # Safe reading again for preview
        file_bytes = uploaded_file.getvalue()
        
        try:
            preview_doc = fitz.open(stream=file_bytes, filetype="pdf")
            first_page = preview_doc[0]
            
            # Apply effect for preview
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
            
            # Show Image
            pix = first_page.get_pixmap(dpi=100)
            st.image(pix.tobytes(), caption="Preview of Page 1", use_container_width=True)
            preview_doc.close()
            
        except Exception as e:
            st.error(f"Error generating preview: {e}")