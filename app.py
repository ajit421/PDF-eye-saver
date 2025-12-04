import streamlit as st
import fitz  # PyMuPDF

# --- Helper Functions ---
def hex_to_rgb(hex_color):
    """Converts hex color ('#RRGGBB') to a tuple (r, g, b) with values 0-1."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def change_pdf_background(file_bytes, color_hex, is_overlay=False):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    rgb_color = hex_to_rgb(color_hex)

    for page in doc:
        rect = page.rect
        shape = page.new_shape()
        
        if is_overlay:
            shape.draw_rect(rect)
            shape.finish(fill=rgb_color, fill_opacity=0.3, color=None) 
            shape.commit(overlay=True)
        else:
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
* **Overlay Mode:** Best for scanned papers.
""")

# Layout: Left for Settings, Right for Preview
col1, col2 = st.columns([1, 1])

# --- LEFT COLUMN (Inputs & Download Button) ---
with col1:
    st.subheader("Upload PDF")
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

    # Pick a color
    color_hex = st.color_picker("Pick a Background Color", "#FFFFCC") 
    
    # Checkbox for Overlay
    is_overlay = st.checkbox("Enable Overlay Mode (For Scanned PDFs)", value=False)
    
    if is_overlay:
        st.info("Overlay mode adds a 'Overlay' on top of the page.")

    # Process Button
    process_btn = st.button("Process PDF", type="primary")

    # --- LOGIC MOVED HERE (So button appears in Col 1) ---
    if process_btn and uploaded_file is not None:
        # We read the file safely
        file_bytes = uploaded_file.getvalue()
        
        with st.spinner("Processing..."):
            try:
                # Call function
                modified_doc = change_pdf_background(file_bytes, color_hex, is_overlay)
                modified_pdf_bytes = modified_doc.tobytes()
                modified_doc.close()
                
                # Show Success & Balloons HERE
                st.balloons()
                st.success("Processing Complete!")
                
                # Dynamic Filename
                original_name = uploaded_file.name
                new_name = f"colored_{original_name}"
                
                # Download Button - Now it appears right under "Process PDF"
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
        st.subheader("Preview PDF")
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
                shape.finish(fill=rgb_color, fill_opacity=0.3, color=None)
                shape.commit(overlay=True)
            else:
                shape.draw_rect(rect)
                shape.finish(fill=rgb_color, color=rgb_color)
                shape.commit(overlay=False)
            
            # Show Image
            pix = first_page.get_pixmap(dpi=100)
            st.image(pix.tobytes(), caption="Preview of Page 1", width=400)
            preview_doc.close()
            
        except Exception as e:
            st.error(f"Error generating preview: {e}")