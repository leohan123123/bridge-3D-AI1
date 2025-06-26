# Placeholder for drawing_templates.py

# In a real application, these would be more complex SVG templates
# with placeholders for data insertion.

GENERAL_ARRANGEMENT_TEMPLATE = """
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font-family: Arial, sans-serif; font-size: 20px; font-weight: bold; }}
        .label {{ font-family: Arial, sans-serif; font-size: 12px; }}
        .structure {{ stroke: black; stroke-width: 2; fill: none; }}
        .dimension {{ stroke: red; stroke-width: 1; fill: none; }}
        .dim-text {{ font-family: Arial, sans-serif; font-size: 10px; fill: red; }}
    </style>
    <rect x="0" y="0" width="{width}" height="{height}" fill="white" stroke="black"/>

    <!-- Title Block -->
    <rect x="{width_minus_200}" y="{height_minus_100}" width="190" height="90" fill="none" stroke="black"/>
    <text x="{width_minus_195}" y="{height_minus_80}" class="title">Drawing Title: {drawing_title}</text>
    <text x="{width_minus_195}" y="{height_minus_60}" class="label">Scale: {scale}</text>
    <text x="{width_minus_195}" y="{height_minus_40}" class="label">Date: {date}</text>

    <!-- Drawing Content Placeholder -->
    {drawing_content}

</svg>
"""

SECTION_VIEW_TEMPLATE = """
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <style>
        .title {{ font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; }}
        .label {{ font-family: Arial, sans-serif; font-size: 10px; }}
        .rebar {{ stroke: blue; stroke-width: 1; }}
        .concrete {{ stroke: gray; stroke-width: 2; fill: lightgray; }}
        .dimension {{ stroke: red; stroke-width: 1; fill: none; }}
        .dim-text {{ font-family: Arial, sans-serif; font-size: 10px; fill: red; }}
    </style>
    <rect x="0" y="0" width="{width}" height="{height}" fill="white" stroke="black"/>

    <!-- Title Block -->
    <rect x="{width_minus_150}" y="{height_minus_80}" width="140" height="70" fill="none" stroke="black"/>
    <text x="{width_minus_145}" y="{height_minus_65}" class="title">{drawing_title}</text>
    <text x="{width_minus_145}" y="{height_minus_50}" class="label">Scale: {scale}</text>

    <!-- Drawing Content Placeholder -->
    {drawing_content}

</svg>
"""

# Helper to populate templates - in a real scenario, this would be more sophisticated
def get_populated_template(template_name: str, data: dict) -> str:
    if template_name == "general_arrangement":
        # Calculate dynamic positions for title block
        data['width_minus_200'] = data.get('width', 800) - 200
        data['height_minus_100'] = data.get('height', 600) - 100
        return GENERAL_ARRANGEMENT_TEMPLATE.format(**data)
    elif template_name == "section_view":
        data['width_minus_150'] = data.get('width', 400) - 150
        data['height_minus_80'] = data.get('height', 300) - 80
        return SECTION_VIEW_TEMPLATE.format(**data)
    return f"<svg><!-- Unknown template: {template_name} --></svg>"
