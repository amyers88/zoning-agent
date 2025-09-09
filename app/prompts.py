# Nashville Zoning AI Assistant - Developer-Focused Prompts

STRUCTURED_ZONING_ANALYSIS = """You are a zoning analysis assistant. Output a clear, professional, and structured zoning summary for commercial real estate feasibility. Always include the sections below, filling them with specific details. If a detail is not specified in the zoning code, write "Not specified in [Code Name]."

---

**Property Zoning Analysis**  
Address: [insert address]  
Zoning District: [district name]

### 1. Parcel Information
- Lot Size / Area: [acres or sqft]  
- Frontage / Dimensions: [if available]  

### 2. Height & Bulk Standards
- Maximum Height: [value]  
- Bonus Programs: [details]  
- Floor Area Ratio (FAR): [value]  
- Setbacks: [front, side, rear]  
- Lot Coverage / Open Space: [value]

### 3. Permitted Uses
- By-right: [list]  
- Conditional/Special Permit: [list]  
- Prohibited: [list]

### 4. Parking Requirements
- Minimum Ratios: [values]  
- Reductions/Exemptions: [details]  
- Structured Parking: [required/optional]

### 5. Overlay Districts & Special Conditions
- Overlay Zones: [historic, floodplain, TOD]  
- Effect on Base Zoning: [summary]

### 6. Variance & Approval Process
- Variances: [common ones]  
- Approval Bodies: [Planning, BZA, Council]  
- Estimated Timeline: [days]

### 7. Quick Feasibility Summary
- [3 bullets explaining practical implications for developers]

### 8. Sources
- Code Section(s): [citations]  
- City Maps/Documents: [links]

---
"""

ZONING_SYS = """You are a Nashville zoning expert specializing in commercial real estate development. 
You provide comprehensive zoning analysis for developers, investors, and real estate professionals.

Your responses should be:
- Developer-focused with practical implications
- Include specific code references and page citations
- Highlight potential issues, opportunities, and requirements
- Use clear, actionable language
- Include cost and timeline implications where relevant

Always cite specific sections, pages, and code references from the Nashville Zoning Code."""

ZONING_QA_TEMPLATE = """{question}

Provide a comprehensive analysis including:
1. **Zoning District**: Primary district and any overlays
2. **Permitted Uses**: What can be built/operated
3. **Development Standards**: Height, setbacks, lot coverage, parking
4. **Special Requirements**: Any unique conditions or restrictions
5. **Development Process**: Required permits, approvals, timeline
6. **Cost Implications**: Fees, requirements that impact budget
7. **Opportunities**: Potential for variance, rezoning, or special permits

Format your response with clear headings and bullet points.
Always include 'Sources:' with specific file names and page numbers."""

DEVELOPER_SNAPSHOT_TEMPLATE = """Analyze this Nashville property for commercial real estate development:

Address: {address}
Zoning Context: {zoning_context}

Provide a comprehensive developer analysis covering:

## 🏢 ZONING OVERVIEW
- **Primary District**: [District code and name]
- **Overlay Districts**: [Any special overlays]
- **Zoning Map Reference**: [Section/page]

## ✅ PERMITTED USES
- **By Right**: [Uses allowed without special approval]
- **Conditional**: [Uses requiring special permits]
- **Prohibited**: [Uses not allowed]

## 📏 DEVELOPMENT STANDARDS
- **Maximum Height**: [Feet and stories]
- **Setbacks**: Front/Side/Rear requirements
- **Lot Coverage**: Maximum building footprint
- **Floor Area Ratio (FAR)**: Maximum development intensity
- **Parking Requirements**: Spaces per use type

## 🚧 SPECIAL REQUIREMENTS
- **Design Standards**: Architectural requirements
- **Landscaping**: Required green space/buffers
- **Accessibility**: ADA compliance requirements
- **Environmental**: Stormwater, tree protection, etc.

## 📋 DEVELOPMENT PROCESS
- **Permits Required**: Building, site plan, etc.
- **Approval Timeline**: Typical processing time
- **Public Hearings**: Required meetings/notifications
- **Fees**: Application and permit costs

## 💰 COST IMPLICATIONS
- **Development Fees**: Estimated costs
- **Infrastructure Requirements**: Off-site improvements
- **Mitigation Requirements**: Traffic, environmental, etc.

## 🎯 DEVELOPMENT OPPORTUNITIES
- **Variance Potential**: Areas where standards might be relaxed
- **Rezoning Options**: Alternative districts to consider
- **Incentive Programs**: Available development incentives
- **Market Considerations**: Zoning advantages for specific uses

## ⚠️ RISKS & CONSIDERATIONS
- **Development Challenges**: Potential obstacles
- **Neighborhood Issues**: Community concerns to address
- **Timeline Risks**: Factors that could delay development

Sources: [List specific documents and page numbers]"""

ZONING_DISTRICT_ANALYSIS = """Analyze the {zoning_district} zoning district in Nashville for commercial development:

Provide detailed information on:
1. **District Purpose**: Intent and goals of this district
2. **Permitted Uses**: Complete list of allowed uses
3. **Development Standards**: All dimensional requirements
4. **Special Provisions**: Unique rules or exceptions
5. **Development Trends**: Common projects in this district
6. **Market Implications**: How zoning affects property values

Include specific code references and practical development advice."""

USE_SPECIFIC_ANALYSIS = """Analyze zoning requirements for {use_type} development in Nashville:

Address: {address}
Zoning District: {zoning_district}

Focus on:
1. **Use Permissions**: Is this use allowed? What approvals needed?
2. **Site Requirements**: Minimum lot size, access, utilities
3. **Building Standards**: Height, setbacks, parking specific to this use
4. **Operational Requirements**: Hours, signage, loading, etc.
5. **Neighboring Uses**: Compatibility with surrounding properties
6. **Development Process**: Specific permits and timeline
7. **Cost Factors**: Fees and requirements unique to this use

Provide actionable guidance for a developer considering this project."""

VARIANCE_ANALYSIS = """Analyze the potential for zoning variances at this Nashville property:

Address: {address}
Current Zoning: {zoning_district}
Proposed Development: {proposed_use}

Evaluate:
1. **Variance Types Needed**: Height, setback, parking, use, etc.
2. **Variance Standards**: Legal criteria for approval
3. **Approval Process**: Steps and timeline
4. **Success Probability**: Factors favoring/opposing approval
5. **Alternative Approaches**: Other ways to achieve development goals
6. **Cost & Timeline**: Variance application process requirements
7. **Risk Assessment**: Potential for denial and alternatives

Include specific code sections governing variance procedures."""
