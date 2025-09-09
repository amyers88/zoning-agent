import json
import requests
import streamlit as st
from pathlib import Path
from string import Template

# Custom CSS for better typography and layout
st.markdown("""
    <style>
        /* Set Times New Roman as the primary font */
        * {
            font-family: 'Times New Roman', Times, serif !important;
        }
        
        /* Main title styling */
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 1.5rem;
        }
        
        /* Section headers */
        h2 {
            color: #2c3e50;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        
        /* Cards for different sections */
        .card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Better spacing for form elements */
        .stTextInput, .stCheckbox {
            margin-bottom: 1rem;
        }
        
        /* Facts list styling */
        .fact-category {
            font-weight: bold;
            color: #2c3e50;
            margin-top: 1rem;
        }
        
        .fact-item {
            margin: 0.5rem 0;
            padding-left: 1rem;
            border-left: 2px solid #e0e0e0;
        }
        
        /* Source list styling */
        .source-item {
            font-size: 0.9rem;
            color: #666;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background-color: #f1f3f5;
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="Nashville Zoning AI",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("Nashville Zoning AI Assistant")

# Sidebar for inputs
with st.sidebar:
    st.header("Analysis Parameters")
    backend = st.text_input("Backend URL", value="http://localhost:8001", help="Change if your API runs elsewhere")
    address = st.text_input("Property Address", value="100 Broadway, Nashville, TN")
    proposed_use = st.text_input("Proposed Use (Optional)", placeholder="e.g., mixed-use development, single-family home")
    include_variance = st.checkbox("Include Variance Analysis", value=False, help="Check to include variance potential and process")
    
    if st.button("Analyze Property", type="primary", use_container_width=True):
        st.session_state.analyze_clicked = True
    else:
        if 'analyze_clicked' not in st.session_state:
            st.session_state.analyze_clicked = False

def load_renderer_template():
    """Load the renderer template from file"""
    template_path = Path(__file__).parent / "app" / "renderer_prompt.md"
    try:
        with open(template_path, 'r') as f:
            # Read the entire template content
            content = f.read()
            # Find the start of the template (after the instructions)
            template_start = content.find('**Property Zoning Analysis**')
            if template_start == -1:
                return content  # Return as is if we can't find the marker
            return content[template_start:]
    except Exception as e:
        st.error(f"Error loading renderer template: {e}")
        return None

def render_report(template, data):
    """Render the report using the template and data"""
    try:
        # Convert data to dict if it's a string
        if isinstance(data, str):
            data = json.loads(data)
        
        # Helper functions for template
        def or_filter(value, default):
            return value if value is not None and value != '' else default
            
        def list_or(value, default):
            if not value:
                return default
            if isinstance(value, list):
                return ', '.join(str(v) for v in value) if value else default
            return str(value)
        
        def bool_or(value, default):
            if value is None:
                return default
            return 'Yes' if value else 'No'
        
        # Create a template with our custom filters
        template = (
            template
            .replace('{', '{{')
            .replace('}', '}}')
            .replace('[[', '{')
            .replace(']]', '}')
            .replace('| or:', '|or:')
            .replace('| listOr:', '|listOr:')
            .replace('| boolOr:', '|boolOr:')
        )
        
        # Add our helper functions to the data
        data['or'] = or_filter
        data['listOr'] = list_or
        data['boolOr'] = bool_or
        
        # Format the template with the data
        report = template.format(**data)
        return report
        
    except Exception as e:
        st.error(f"Error rendering report: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Main content
if st.session_state.analyze_clicked:
    with st.spinner("Analyzing property details..."):
        try:
            # Load the renderer template
            template = load_renderer_template()
            if not template:
                st.error("Failed to load renderer template")
                st.stop()
                
            payload = {
                "address": address,
                "include_variance_analysis": include_variance
            }
            if proposed_use:
                payload["proposed_use"] = proposed_use
                
            # Make API call
            response = requests.post(f"{backend}/analyze", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Store the raw data in session state
            st.session_state.analysis_data = data
            
            # Render the report
            report = render_report(template, data)
            
            if report:
                st.markdown("## Zoning Analysis Report")
                st.markdown(report, unsafe_allow_html=True)
                
                # Add a download button for the report
                st.download_button(
                    label="Download Report as Markdown",
                    data=report,
                    file_name="zoning_analysis_report.md",
                    mime="text/markdown"
                )
                
                # Show raw data in an expander for debugging
                with st.expander("View Raw Data"):
                    st.json(data)
            else:
                st.error("Failed to generate report")
        except Exception as e:
            st.error(f"Error analyzing property: {str(e)}")
            st.stop()
    
    # Display results if we have data
    if 'analysis_data' in st.session_state and st.session_state.analysis_data:
        data = st.session_state.analysis_data
        
        # Property Overview Card
        st.markdown("### Property Overview")
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown(f"**Address:** {data.get('address', 'N/A')}")
            st.markdown(f"**Zoning District:** `{data.get('zoning_district', 'Unknown')}`")
            if data.get("coordinates"):
                lat, lon = data["coordinates"]
                st.markdown(f"**Location:** {lat:.5f}°N, {lon:.5f}°W")
        
        with col2:
            if data.get("coordinates"):
                try:
                    m = requests.post(
                        f"{backend}/map/static",
                        json={"address": address},
                        timeout=30
                    )
                    if m.ok and m.json().get("map_url"):
                        st.image(
                            m.json().get("map_url"),
                            caption=f"Location: {address}",
                            use_column_width=True
                        )
                except:
                    pass
        
        st.markdown("---")
        
        # Analysis Section
        st.markdown("### Zoning Analysis")
        st.markdown("<div class='card'>" + data.get("detailed_analysis", "No analysis available.").replace("\n", "<br>") + "</div>", unsafe_allow_html=True)
        
        # Facts Section
        if data.get("facts"):
            st.markdown("### Key Facts & Requirements")
            facts_col1, facts_col2 = st.columns(2)
            
            with facts_col1:
                for category, items in data["facts"].items():
                    if isinstance(items, dict):
                        st.markdown(f"<div class='fact-category'>{category.replace('_', ' ').title()}</div>", unsafe_allow_html=True)
                        if isinstance(items, dict):
                            for key, value in items.items():
                                if value:  # Only show if value exists
                                    st.markdown(f"<div class='fact-item'><b>{key.replace('_', ' ').title()}:</b> {value}</div>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
            
            with facts_col2:
                # Handle any remaining facts that might not fit in the first column
                # This could be expanded based on specific fact categories you want to separate
                pass
        
        # Sources Section
        if data.get("sources"):
            st.markdown("### Reference Sources")
            st.markdown("<div class='card'><p>This analysis was generated using the following sources:</p>", unsafe_allow_html=True)
            
            for source in data.get("sources", [])[:5]:  # Limit to top 5 sources
                source_text = f"{source.get('source', 'Unknown')}"
                if source.get('page'):
                    source_text += f" (Page {source['page']})"
                st.markdown(f"<div class='source-item'>{source_text}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.caption("Analysis generated on " + data.get("analysis_timestamp", "unknown date"))
        st.caption("Powered by Ollama + ChromaDB | Nashville Zoning AI")
else:
    # Initial state before analysis
    st.markdown("""
        <div class='card'>
            <h3>Welcome to the Nashville Zoning AI Assistant</h3>
            <p>This tool helps you analyze zoning regulations for properties in Nashville, TN.</p>
            <p><b>To get started:</b></p>
            <ol>
                <li>Enter the property address</li>
                <li>Optionally specify a proposed use</li>
                <li>Check the box to include variance analysis if needed</li>
                <li>Click 'Analyze Property'</li>
            </ol>
            <p>The analysis will provide detailed zoning information, requirements, and development considerations.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Example analysis section
    with st.expander("Example Analysis"):
        st.markdown("""
            <div style='font-family: Times New Roman;'>
                <h4>100 Broadway, Nashville, TN</h4>
                <p><b>Zoning District:</b> DTC (Downtown Code)</p>
                <p><b>Key Findings:</b></p>
                <ul>
                    <li>Permitted uses include mixed-use development with commercial, residential, and office components</li>
                    <li>Maximum height allowance: 30 stories with bonus provisions</li>
                    <li>Minimum parking requirements may be reduced with proximity to transit</li>
                    <li>Special design guidelines apply in the Downtown Code area</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)



