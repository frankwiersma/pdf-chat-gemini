import streamlit as st
import os
import time
import random
import string
import tempfile
import json
from pathlib import Path
from datetime import datetime
from PyPDF2 import PdfReader
from google import genai
from google.genai import types
from dotenv import load_dotenv

# App text
APP_TEXT = {
    'page_title': 'PDF Chat with Gemini AI',
    'page_icon': '📚',
    'main_title': '📚 Intelligent PDF Chat Assistant',
    'subtitle': "Powered by Google's Gemini AI - Upload any PDF and have an intelligent conversation about its content",
    'model': 'AI Model',
    'api_key_label': 'Enter your Gemini API Key',
    'api_key_help': 'Get your free API key from https://makersuite.google.com/app/apikey',
    'api_key_warning': 'Security Notice',
    'api_key_warning_text': 'Your API key is stored only in your browser session and is never saved or shared. Keep your API key private.',
    'api_key_required': 'Please enter your Gemini API key in the sidebar to get started',
    'sidebar_header': 'Document Upload',
    'choose_file': 'Choose a PDF file',
    'processing': 'Processing your document...',
    'upload_success': 'Successfully uploaded: {}',
    'current_pdf': 'Current Document: {}',
    'clear_button': 'Clear Document & Start Over',
    'about_header': 'About This App',
    'about_text': "This intelligent assistant uses Google's Gemini AI with advanced File Search capabilities to help you explore and understand your PDF documents through natural conversation.",
    'upload_prompt': 'Upload a PDF file from the sidebar to begin your intelligent conversation',
    'chat_input': 'Ask me anything about your document...',
    'thinking': 'Analyzing...',
    'view_sources': 'View Source References',
    'error_response': "I couldn't generate a response. Please try rephrasing your question.",
    'footer': 'Built with Streamlit and Google Gemini AI',
    'error_api_key': 'API key is required.',
    'error_pdf_extract': 'Error extracting text from PDF: {}',
    'error_save_file': 'Error saving file: {}',
    'error_create_store': 'Error creating file search store: {}',
    'error_upload_store': 'Error uploading file to store: {}',
    'error_query': 'Error querying file search: {}',
    'error_cleanup': 'Error cleaning up store: {}',
    'pdf_info': 'Document Information',
    'pages': 'Pages',
    'file_size': 'File Size',
    'uploaded_at': 'Uploaded',
    'export_chat': 'Export Chat History',
    'clear_chat': 'Clear Chat History',
    'suggested_questions': 'Suggested Questions',
    'stats_header': 'Session Statistics',
    'total_questions': 'Questions Asked',
    'copy_response': 'Copy',
    'copied': 'Copied!'
}

def get_text(key):
    """Get text for the given key"""
    return APP_TEXT.get(key, key)

# Helper Functions
def generate_random_id(length=8):
    """Generate a random ID for store naming"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def wait_operation(client, op, sleep_sec=2, max_wait_sec=300):
    """Wait for Operations API to complete with timeout"""
    start = time.time()
    while not op.done:
        if time.time() - start > max_wait_sec:
            raise TimeoutError("Operation timed out.")
        time.sleep(sleep_sec)
        op = client.operations.get(op)
    return op

def extract_text_from_pdf(pdf_file):
    """Extract text content from uploaded PDF file"""
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text, len(pdf_reader.pages)
    except Exception as e:
        st.error(get_text('error_pdf_extract').format(e))
        return None, 0

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary location"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(get_text('error_save_file').format(e))
        return None

def create_file_search_store(client, store_name):
    """Create a new File Search Store"""
    try:
        store = client.file_search_stores.create(
            config={'display_name': store_name}
        )
        return store
    except Exception as e:
        st.error(get_text('error_create_store').format(e))
        return None

def upload_file_to_store(client, file_path, store_name, display_name):
    """Upload file to File Search Store with size validation"""
    try:
        # Check file size (Gemini API has a 5MB limit for some operations)
        file_size = os.path.getsize(file_path)
        max_size = 5 * 1024 * 1024  # 5MB in bytes

        if file_size > max_size:
            st.warning(f"⚠️ Large file detected ({format_file_size(file_size)}). This may take longer to process or fail with large PDFs. Consider using a smaller file.")

        upload_op = client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=store_name,
            config={
                'display_name': display_name,
                'custom_metadata': [
                    {"key": "source", "string_value": "streamlit_upload"},
                    {"key": "timestamp", "numeric_value": int(time.time())}
                ]
            }
        )
        upload_op = wait_operation(client, upload_op, max_wait_sec=600)  # Increase timeout for large files
        return upload_op.response
    except TimeoutError as e:
        st.error("⏱️ Upload timed out. The file may be too large. Try a smaller PDF (under 2-3 MB recommended).")
        return None
    except Exception as e:
        error_msg = str(e)
        if "400" in error_msg or "bad request" in error_msg.lower():
            st.error(f"❌ Bad Request: The file may be too large or in an unsupported format. Try a smaller PDF (under 2 MB recommended). Error: {e}")
        elif "413" in error_msg or "too large" in error_msg.lower():
            st.error(f"📦 File too large: Try a PDF under 2 MB. Error: {e}")
        else:
            st.error(get_text('error_upload_store').format(e))
        return None

def query_file_search(client, question, store_name, model):
    """Query the File Search Store with a question"""
    try:
        response = client.models.generate_content(
            model=model,
            contents=question,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ]
            )
        )
        return response
    except Exception as e:
        st.error(get_text('error_query').format(e))
        return None

def cleanup_store(client, store_name):
    """Delete the File Search Store"""
    try:
        client.file_search_stores.delete(
            name=store_name,
            config={'force': True}
        )
        return True
    except Exception as e:
        st.error(get_text('error_cleanup').format(e))
        return False

def export_chat_history(chat_history):
    """Export chat history as JSON"""
    export_data = {
        'exported_at': datetime.now().isoformat(),
        'conversation': chat_history
    }
    return json.dumps(export_data, indent=2)

def get_suggested_questions(pdf_name):
    """Generate suggested questions based on PDF type"""
    suggestions = [
        "What are the main topics covered in this document?",
        "Can you provide a summary of the key points?",
        "What are the most important findings or conclusions?",
        "Are there any specific recommendations or action items mentioned?"
    ]
    return suggestions

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

# Streamlit UI
st.set_page_config(
    page_title=get_text('page_title'),
    page_icon=get_text('page_icon'),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 500;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'store_name' not in st.session_state:
    st.session_state.store_name = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = None
if 'model' not in st.session_state:
    st.session_state.model = 'gemini-2.5-flash'
if 'pdf_pages' not in st.session_state:
    st.session_state.pdf_pages = 0
if 'pdf_size' not in st.session_state:
    st.session_state.pdf_size = 0
if 'upload_time' not in st.session_state:
    st.session_state.upload_time = None
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

# Header
st.markdown(f"""
<div class="main-header">
    <h1>{get_text('main_title')}</h1>
    <p>{get_text('subtitle')}</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for PDF upload
with st.sidebar:
    # API Key input
    st.subheader("🔑 API Configuration")
    api_key_input = st.text_input(
        get_text('api_key_label'),
        type="password",
        help=get_text('api_key_help')
    )

    # Security warning
    with st.expander(get_text('api_key_warning')):
        st.caption(get_text('api_key_warning_text'))

    # Check API key
    if not api_key_input:
        st.warning(get_text('api_key_required'))
        st.stop()

    # Initialize Gemini client with user's API key
    try:
        client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.error(f"API Key Error: {e}")
        st.stop()

    # Model selector
    model_options = [
        'gemini-2.5-flash',
        'gemini-2.5-pro'
    ]
    selected_model = st.selectbox(
        get_text('model'),
        options=model_options,
        index=model_options.index(st.session_state.model),
        help="Choose the AI model for processing your documents"
    )
    st.session_state.model = selected_model

    st.markdown("---")
    st.header(get_text('sidebar_header'))

    uploaded_file = st.file_uploader(get_text('choose_file'), type=['pdf'])

    if uploaded_file is not None and not st.session_state.pdf_uploaded:
        with st.spinner(get_text('processing')):
            # Save uploaded file
            temp_file_path = save_uploaded_file(uploaded_file)

            if temp_file_path:
                # Get PDF metadata
                file_size = len(uploaded_file.getvalue())
                st.session_state.pdf_size = file_size
                st.session_state.upload_time = datetime.now()

                # Extract page count
                text, page_count = extract_text_from_pdf(uploaded_file)
                st.session_state.pdf_pages = page_count

                # Create unique store name
                unique_id = generate_random_id()
                store_display_name = f'pdf-chat-store-{unique_id}'

                # Create file search store
                store = create_file_search_store(client, store_display_name)

                if store:
                    # Upload file to store
                    file_display_name = Path(uploaded_file.name).stem
                    uploaded = upload_file_to_store(
                        client,
                        temp_file_path,
                        store.name,
                        file_display_name
                    )

                    if uploaded:
                        st.session_state.store_name = store.name
                        st.session_state.pdf_uploaded = True
                        st.session_state.pdf_name = uploaded_file.name
                        st.success(get_text('upload_success').format(uploaded_file.name))

                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass

    if st.session_state.pdf_uploaded:
        # PDF Information Box
        st.markdown("### 📊 " + get_text('pdf_info'))
        st.markdown(f"""
        <div class="info-box">
            <strong>{get_text('current_pdf')}</strong><br/>
            {st.session_state.pdf_name}<br/><br/>
            <strong>{get_text('pages')}:</strong> {st.session_state.pdf_pages}<br/>
            <strong>{get_text('file_size')}:</strong> {format_file_size(st.session_state.pdf_size)}<br/>
            <strong>{get_text('uploaded_at')}:</strong> {st.session_state.upload_time.strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        # Session Statistics
        st.markdown("### 📈 " + get_text('stats_header'))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <h2 style="margin:0;">{st.session_state.question_count}</h2>
                <p style="margin:0;">{get_text('total_questions')}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <h2 style="margin:0;">{len(st.session_state.chat_history)//2}</h2>
                <p style="margin:0;">Exchanges</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Export and Clear buttons
        col1, col2 = st.columns(2)
        with col1:
            if len(st.session_state.chat_history) > 0:
                export_data = export_chat_history(st.session_state.chat_history)
                st.download_button(
                    label="💾 " + get_text('export_chat'),
                    data=export_data,
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        with col2:
            if st.button("🗑️ " + get_text('clear_button')):
                # Cleanup store
                if st.session_state.store_name:
                    cleanup_store(client, st.session_state.store_name)

                # Reset session state
                st.session_state.store_name = None
                st.session_state.chat_history = []
                st.session_state.pdf_uploaded = False
                st.session_state.pdf_name = None
                st.session_state.pdf_pages = 0
                st.session_state.pdf_size = 0
                st.session_state.upload_time = None
                st.session_state.question_count = 0
                st.rerun()

    st.markdown("---")
    st.markdown("### " + get_text('about_header'))
    st.markdown(get_text('about_text'))

# Main chat interface
if not st.session_state.pdf_uploaded:
    st.info(get_text('upload_prompt'))

    # Welcome message with features
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🎯 Key Features
        - Advanced AI-powered search
        - Natural conversation
        - Source references
        """)
    with col2:
        st.markdown("""
        ### 🚀 How It Works
        1. Upload your PDF
        2. Ask questions
        3. Get instant answers
        """)
    with col3:
        st.markdown("""
        ### 💡 Capabilities
        - Summarization
        - Deep analysis
        - Information extraction
        """)
else:
    # Suggested questions (show only if no chat history)
    if len(st.session_state.chat_history) == 0:
        st.markdown("### 💡 " + get_text('suggested_questions'))
        suggestions = get_suggested_questions(st.session_state.pdf_name)
        cols = st.columns(2)
        for idx, suggestion in enumerate(suggestions):
            with cols[idx % 2]:
                if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
                    # Set pending question to be processed below
                    st.session_state.pending_question = suggestion
                    st.session_state.question_count += 1
                    st.rerun()

    # Display chat history
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Add copy button for assistant responses
            if message["role"] == "assistant":
                if st.button(get_text('copy_response'), key=f"copy_{idx}", type="secondary"):
                    st.toast(get_text('copied'))

    # Process pending question from suggested questions
    if st.session_state.pending_question:
        prompt = st.session_state.pending_question
        st.session_state.pending_question = None  # Clear it

        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(get_text('thinking')):
                response = query_file_search(client, prompt, st.session_state.store_name, st.session_state.model)

                if response and response.text:
                    st.markdown(response.text)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response.text
                    })

                    # Show grounding metadata if available
                    try:
                        gm = response.candidates[0].grounding_metadata
                        if gm:
                            with st.expander(get_text('view_sources')):
                                st.write(gm)
                    except:
                        pass
                else:
                    error_msg = get_text('error_response')
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Chat input
    if prompt := st.chat_input(get_text('chat_input')):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.question_count += 1

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(get_text('thinking')):
                response = query_file_search(client, prompt, st.session_state.store_name, st.session_state.model)

                if response and response.text:
                    st.markdown(response.text)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response.text
                    })

                    # Show grounding metadata if available
                    try:
                        gm = response.candidates[0].grounding_metadata
                        if gm:
                            with st.expander(get_text('view_sources')):
                                st.write(gm)
                    except:
                        pass
                else:
                    error_msg = get_text('error_response')
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666;">
    {get_text('footer')}<br/>
    <small>Made with ❤️ using Streamlit & Google Gemini AI</small>
</div>
""", unsafe_allow_html=True)
