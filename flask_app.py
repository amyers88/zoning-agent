from flask import Flask, render_template_string, send_from_directory, jsonify
import os
import json
import re
from typing import Dict, List, Optional, Any

app = Flask(__name__, static_folder='static')

# Create static directory if it doesn't exist
os.makedirs('static', exist_ok=True)

# Simple HTML template with our styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Nashville Zoning AI</title>
    <style>
        * {
            font-family: 'Times New Roman', Times, serif !important;
        }
        body {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 1.5rem;
        }
        .container {
            display: flex;
            gap: 20px;
        }
        .sidebar {
            width: 300px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .main-content {
            flex: 1;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"], textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #2980b9;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .fact-section {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .fact-section:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .sources {
            list-style-type: none;
            padding-left: 0;
        }
        .sources a {
            color: #3498db;
            text-decoration: none;
        }
        .sources a:hover {
            text-decoration: underline;
        }
        .summary {
            margin-bottom: 10px;
        }
        .explanation {
            background-color: #f8f9fa;
            border-left: 3px solid #3498db;
            padding: 10px 15px;
            margin: 10px 0;
            font-style: italic;
        }
        .details {
            margin-top: 10px;
        }
        .toggle-details {
            background: none;
            border: 1px solid #3498db;
            color: #3498db;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .toggle-details:hover {
            background-color: #f0f7ff;
        }
        .details-content {
            background-color: #f8f9fa;
            padding: 10px 15px;
            border-radius: 4px;
            margin-top: 5px;
            border: 1px solid #eee;
        }
        .error {
            color: #e74c3c;
            background-color: #fde8e8;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>Nashville Zoning AI</h1>
    
    <div class="container">
        <div class="sidebar">
            <h2>Analysis Parameters</h2>
            <div class="form-group">
                <label for="address">Property Address</label>
                <input type="text" id="address" value="100 Broadway, Nashville, TN">
            </div>
            <div class="form-group">
                <label for="use">Proposed Use (Optional)</label>
                <input type="text" id="use" placeholder="e.g., mixed-use development">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="variance"> Include Variance Analysis
                </label>
            </div>
            <button onclick="analyze()">Analyze Property</button>
        </div>
        
        <div class="main-content">
            <div class="card">
                <h2>Zoning Analysis</h2>
                <p>Enter an address and click "Analyze Property" to get started.</p>
                <div id="analysis-results"></div>
            </div>
            
            <div class="card">
                <h2>Key Facts & Requirements</h2>
                <div id="facts"></div>
            </div>
        </div>
    </div>

    <script>
    // Load and display data when the page loads
    document.addEventListener('DOMContentLoaded', function() {
        // Set up the analyze button
        document.querySelector('button').addEventListener('click', analyze);
        
        // Initial load of data
        loadZoningData();
    });
    
    function loadZoningData() {
        // Show loading state
        document.getElementById('analysis-results').innerHTML = '<p>Analyzing property... This may take a moment.</p>';
        document.getElementById('facts').innerHTML = '';
        
        fetch('/get_zoning_data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                updateUI(data);
            })
            .catch(error => {
                console.error('Error loading zoning data:', error);
                document.getElementById('analysis-results').innerHTML = `
                    <div class="error">
                        <h3>Error</h3>
                        <p>Could not load zoning data. Please try again later.</p>
                        <p>${error.message}</p>
                    </div>`;
            });
    }
    
    function analyze() {
        const address = document.getElementById('address').value;
        const use = document.getElementById('use').value;
        const includeVariance = document.getElementById('variance').checked;
        
        // Show loading state
        document.getElementById('analysis-results').innerHTML = '<p>Analyzing property... This may take a moment.</p>';
        document.getElementById('facts').innerHTML = '';
        
        // In a real app, you would make an API call here
        // For now, we'll just reload the data
        loadZoningData();
    }
    
    function updateUI(data) {
        const address = document.getElementById('address').value;
        const use = document.getElementById('use').value;
        const includeVariance = document.getElementById('variance').checked;
        
        // Display address and district
        let analysisHtml = `
            <h3>Analysis for ${data.address || address}</h3>
            <p><strong>Zoning District:</strong> ${data.district || 'Not specified'}</p>`;
            
        if (use) {
            analysisHtml += `<p><strong>Proposed Use:</strong> ${use}</p>`;
        }
        
        if (includeVariance) {
            analysisHtml += `<p><strong>Variance Analysis:</strong> Included</p>`;
        }
        
        document.getElementById('analysis-results').innerHTML = analysisHtml;
        
        // Display key facts
        let factsHtml = '';
        
        // Height section
        if (data.sections && data.sections.height) {
            const height = data.sections.height;
            factsHtml += `
                <div class="fact-section">
                    <h3>Height Requirements</h3>`;
            
            if (height.summary && height.summary.length > 0) {
                factsHtml += `
                    <ul class="summary">
                        ${Array.isArray(height.summary) ? 
                          height.summary.map(item => `<li>${item}</li>`).join('') : 
                          `<li>${height.summary}</li>`}
                    </ul>`;
                
                if (height.explanation) {
                    factsHtml += `
                    <div class="explanation">
                        <p><em>${height.explanation}</em></p>
                    </div>`;
                }
                
                // Show details if available
                if (height.details && height.details.length > 0) {
                    factsHtml += `
                    <div class="details">
                        <button class="toggle-details" onclick="toggleDetails(this)">Show Details</button>
                        <div class="details-content" style="display: none;">
                            <h4>Detailed Information:</h4>
                            <ul>
                                ${height.details.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    </div>`;
                }
            } else {
                factsHtml += `<p>No height requirements specified.</p>`;
            }
            
            factsHtml += `</div>`; // Close fact-section
        }
        
        // Uses section
        if (data.sections && data.sections.uses) {
            const uses = data.sections.uses;
            factsHtml += `
                <div class="fact-section">
                    <h3>Permitted Uses</h3>`;
            
            if (uses.summary && uses.summary.length > 0) {
                factsHtml += `
                    <ul class="summary">
                        ${Array.isArray(uses.summary) ? 
                          uses.summary.map(item => `<li>${item}</li>`).join('') : 
                          `<li>${uses.summary}</li>`}
                    </ul>`;
                
                if (uses.explanation) {
                    factsHtml += `
                    <div class="explanation">
                        <p><em>${uses.explanation}</em></p>
                    </div>`;
                }
                
                // Show details if available
                if (uses.details && uses.details.length > 0) {
                    factsHtml += `
                    <div class="details">
                        <button class="toggle-details" onclick="toggleDetails(this)">Show Details</button>
                        <div class="details-content" style="display: none;">
                            <h4>Detailed Information:</h4>
                            <ul>
                                ${uses.details.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    </div>`;
                }
            } else {
                factsHtml += `<p>No specific use restrictions found.</p>`;
            }
            
            factsHtml += `</div>`; // Close fact-section
        }
        
        // Parking section
        if (data.sections && data.sections.parking) {
            const parking = data.sections.parking;
            factsHtml += `
                <div class="fact-section">
                    <h3>Parking Requirements</h3>`;
            
            if (parking.summary && parking.summary.length > 0) {
                factsHtml += `
                    <ul class="summary">
                        ${Array.isArray(parking.summary) ? 
                          parking.summary.map(item => `<li>${item}</li>`).join('') : 
                          `<li>${parking.summary}</li>`}
                    </ul>`;
                
                if (parking.explanation) {
                    factsHtml += `
                    <div class="explanation">
                        <p><em>${parking.explanation}</em></p>
                    </div>`;
                }
                
                // Show details if available
                if (parking.details && parking.details.length > 0) {
                    factsHtml += `
                    <div class="details">
                        <button class="toggle-details" onclick="toggleDetails(this)">Show Details</button>
                        <div class="details-content" style="display: none;">
                            <h4>Detailed Information:</h4>
                            <ul>
                                ${parking.details.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    </div>`;
                }
            } else {
                factsHtml += `<p>No specific parking requirements found.</p>`;
            }
            
            factsHtml += `</div>`; // Close fact-section
        }
        
        // Sources section (always show if sources exist)
        if (data.sources && data.sources.length > 0) {
            factsHtml += `
                <div class="fact-section">
                    <h3>Sources</h3>
                    <p>The following documents were used in this analysis:</p>
                    <ul class="sources">
                        ${data.sources.map(source => {
                            const url = source.url || '#';
                            const displayText = source.title || 'Source';
                            return `<li><a href="${url}" target="_blank">${displayText}</a></li>`;
                        }).join('')}
                    </ul>
                </div>`;
        } else {
            factsHtml += `
                <div class="fact-section">
                    <h3>Sources</h3>
                    <p>No source documents were referenced for this analysis.</p>
                </div>`;
        }
        
        document.getElementById('facts').innerHTML = factsHtml;
    }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

def summarize_height(height_data: List[str]) -> Dict[str, Any]:
    """Summarize height requirements from raw text data."""
    if not height_data:
        return {
            'summary': 'No height restrictions specified.',
            'explanation': 'No specific height restrictions found for this zoning district.'
        }
    
    # Look for key phrases in the height data
    text = ' '.join(height_data).lower()
    max_height = None
    bonus_info = []
    
    # Extract maximum height
    height_match = re.search(r'(maximum|max) (height|stories?|floors?)[: ]*([0-9.]+)', text)
    if height_match:
        max_height = height_match.group(3)
    
    # Look for bonus height information
    if 'bonus' in text and ('height' in text or 'stories' in text or 'floors' in text):
        bonus_phrases = [
            'in exchange for',
            'with bonus',
            'additional height',
            'bonus height',
            'incentive',
            'in return for'
        ]
        
        # Find sentences containing bonus information
        for line in height_data:
            if any(phrase in line.lower() for phrase in bonus_phrases):
                bonus_info.append(line.strip())
    
    # Generate summary
    summary_parts = []
    if max_height:
        summary_parts.append(f'Maximum height: {max_height} stories')
    if bonus_info:
        summary_parts.append('Bonus height available with public amenities')
    
    explanation = ""
    if max_height and bonus_info:
        explanation = f"You can build up to {max_height} stories, with potential for additional height by providing public amenities or meeting specific criteria."
    elif max_height:
        explanation = f"The maximum allowed height is {max_height} stories with no bonus provisions."
    else:
        explanation = "Height regulations may vary based on specific development criteria."
    
    return {
        'summary': summary_parts,
        'explanation': explanation,
        'details': height_data[:5]  # Include first few details for reference
    }

def summarize_uses(uses_data: List[str]) -> Dict[str, Any]:
    """Summarize permitted uses from raw text data."""
    if not uses_data:
        return {
            'summary': ['No specific use restrictions found.'],
            'explanation': 'No specific use restrictions were identified for this zoning district.'
        }
    
    # Categorize uses
    categories = {
        'Residential': ['residential', 'dwelling', 'apartment', 'condo', 'townhome'],
        'Office': ['office', 'professional', 'business'],
        'Retail': ['retail', 'store', 'shop', 'commercial'],
        'Hospitality': ['hotel', 'motel', 'lodging', 'inn'],
        'Food': ['restaurant', 'cafe', 'bar', 'food service'],
        'Industrial': ['industrial', 'manufacturing', 'warehouse'],
        'Institutional': ['institutional', 'school', 'church', 'place of worship', 'community center']
    }
    
    found_categories = set()
    text = ' '.join(uses_data).lower()
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            found_categories.add(category)
    
    summary = list(found_categories) if found_categories else ['Various uses permitted']
    
    return {
        'summary': summary,
        'explanation': 'These are the primary use categories permitted in this zoning district.',
        'details': uses_data[:5]  # Include first few details for reference
    }

def summarize_parking(parking_data: List[str]) -> Dict[str, Any]:
    """Summarize parking requirements from raw text data."""
    if not parking_data:
        return {
            'summary': ['No specific parking requirements found.'],
            'explanation': 'No specific parking requirements were identified for this zoning district.'
        }
    
    text = ' '.join(parking_data).lower()
    requirements = []
    
    # Look for parking ratios
    ratio_match = re.search(r'([0-9.]+)\s*(parking )?space', text)
    if ratio_match:
        ratio = ratio_match.group(1)
        requirements.append(f'Minimum {ratio} spaces per unit/1,000 sq ft')
    
    # Check for structured parking requirements
    if 'structured' in text or 'garage' in text:
        requirements.append('Structured parking may be required')
    
    # Look for reductions or waivers
    if 'reduction' in text or 'waiver' in text or 'reduce' in text:
        requirements.append('Reductions available for transit-oriented development')
    
    if not requirements:
        requirements = ['Standard parking requirements apply']
    
    explanation = "Parking requirements are based on use type and may be reduced for projects near transit or in designated areas."
    
    return {
        'summary': requirements,
        'explanation': explanation,
        'details': parking_data[:5]  # Include first few details for reference
    }

@app.route('/get_zoning_data')
def get_zoning_data():
    try:
        json_path = os.path.join('data', 'cache', 'last_fetch.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Process and summarize the data
        processed_data = {
            'address': data.get('address', 'Address not available'),
            'district': data.get('district', 'Zoning district not available'),
            'sections': {},
            'sources': data.get('sources', [])
        }
        
        # Process each section if it exists
        sections = data.get('sections', {})
        if 'height' in sections:
            processed_data['sections']['height'] = summarize_height(sections['height'])
        if 'uses' in sections:
            processed_data['sections']['uses'] = summarize_uses(sections['uses'])
        if 'parking' in sections:
            processed_data['sections']['parking'] = summarize_parking(sections['parking'])
        
        return jsonify(processed_data)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'address': 'Error loading address',
            'district': 'Error loading district',
            'sections': {},
            'sources': []
        }), 500

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
