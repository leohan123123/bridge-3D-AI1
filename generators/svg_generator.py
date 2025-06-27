import math

class SVGGenerator:
    def generate_bridge_elevation(self, design_data: dict) -> str:
        """
        Generates a basic SVG elevation view of a bridge.
        Focuses on a single primary span.
        """
        span_length = design_data.get("span_lengths", [50.0])[0] # Assume first span is primary
        girder_depth = design_data.get("main_girder", {}).get("depth_m", 2.0)
        bridge_type_text = design_data.get("bridge_type", "Bridge")

        # SVG Canvas Dimensions & Scaling
        padding = 50
        svg_width = 800
        svg_height = 400 # Adjusted for better proportion with typical girder depths

        # Scale bridge dimensions to fit SVG canvas
        # Scale factor based on span_length to fit svg_width
        content_width = svg_width - 2 * padding
        scale_factor = content_width / span_length if span_length > 0 else 1

        scaled_span = span_length * scale_factor
        scaled_girder_depth = girder_depth * scale_factor

        # Define Y coordinates for drawing (from top down)
        ground_y = svg_height - padding  # Where supports rest
        girder_bottom_y = ground_y - scaled_girder_depth
        girder_top_y = girder_bottom_y - scaled_girder_depth # This is wrong, should be girder_bottom_y

        # Corrected Y coordinates
        # Let's assume supports are a certain height, e.g. 20px
        support_height_svg = 30 * (scale_factor if scale_factor < 1 else 1) # Scaled support height, but not too small
        if support_height_svg < 20: support_height_svg = 20 # Minimum support height
        if support_height_svg > 60: support_height_svg = 60 # Maximum support height


        girder_bottom_y = ground_y - support_height_svg
        girder_top_y = girder_bottom_y - scaled_girder_depth

        # Adjust svg_height if content is too tall, or ensure elements are positioned correctly
        min_drawing_height = scaled_girder_depth + support_height_svg + padding  # top_padding + girder + support + bottom_padding
        if svg_height < min_drawing_height + padding : # Ensure enough space for text too
            svg_height = min_drawing_height + padding + 50 # Add some more for text

        # Start of SVG string
        svg_parts = [
            f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #f0f8ff; border: 1px solid #ccc;">',
            '<style>.dim_text { font-size: 12px; fill: #333; } .title_text { font-size: 16px; font-weight: bold; fill: #003366; } .label_text { font-size: 10px; fill: #555; }</style>',
            f'<text x="{svg_width/2}" y="25" text-anchor="middle" class="title_text">Bridge Elevation: {bridge_type_text}</text>'
        ]

        # Girder/Deck
        girder_x = padding
        svg_parts.append(f'<rect x="{girder_x}" y="{girder_top_y}" width="{scaled_span}" height="{scaled_girder_depth}" fill="#aabbcc" stroke="#555" stroke-width="1"/>')

        # Supports (simple triangles or rectangles)
        support_width_svg = max(10, scaled_girder_depth * 0.5) # Make support width proportional but not too small

        # Left support (triangle)
        svg_parts.append(f'<polygon points="{girder_x - support_width_svg/2},{ground_y} {girder_x + support_width_svg/2},{ground_y} {girder_x},{girder_bottom_y}" fill="#888" stroke="#444"/>')
        # Right support (triangle)
        svg_parts.append(f'<polygon points="{girder_x + scaled_span - support_width_svg/2},{ground_y} {girder_x + scaled_span + support_width_svg/2},{ground_y} {girder_x + scaled_span},{girder_bottom_y}" fill="#888" stroke="#444"/>')

        # Ground line (optional)
        svg_parts.append(f'<line x1="{padding/2}" y1="{ground_y}" x2="{svg_width - padding/2}" y2="{ground_y}" stroke="#654321" stroke-width="2"/>')

        # Dimensions
        # Span Length Dimension Line
        dim_y_span = ground_y + 25 # Below ground line
        if dim_y_span > svg_height -15 : dim_y_span = girder_top_y - 15 # If ground is too low, put above girder

        svg_parts.append(f'<line x1="{girder_x}" y1="{dim_y_span - 5}" x2="{girder_x}" y2="{girder_top_y}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2"/>') # Left tick extension
        svg_parts.append(f'<line x1="{girder_x + scaled_span}" y1="{dim_y_span - 5}" x2="{girder_x + scaled_span}" y2="{girder_top_y}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2"/>') # Right tick extension
        svg_parts.append(f'<line x1="{girder_x}" y1="{dim_y_span}" x2="{girder_x + scaled_span}" y2="{dim_y_span}" stroke="black" stroke-width="1"/>')
        svg_parts.append(f'<text x="{girder_x + scaled_span/2}" y="{dim_y_span - 7}" text-anchor="middle" class="dim_text">Span: {span_length:.2f} m</text>')
        # Arrows for span dimension
        svg_parts.append(f'<polygon points="{girder_x},{dim_y_span} {girder_x+5},{dim_y_span-3} {girder_x+5},{dim_y_span+3}" fill="black"/>')
        svg_parts.append(f'<polygon points="{girder_x+scaled_span},{dim_y_span} {girder_x+scaled_span-5},{dim_y_span-3} {girder_x+scaled_span-5},{dim_y_span+3}" fill="black"/>')


        # Girder Depth Dimension Line (Vertical)
        dim_x_depth = girder_x - 15
        if dim_x_depth < 15 : dim_x_depth = girder_x + scaled_span + 15 # If too close to left edge, put on right

        svg_parts.append(f'<line x1="{dim_x_depth + 5}" y1="{girder_top_y}" x2="{girder_x}" y2="{girder_top_y}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2"/>')
        svg_parts.append(f'<line x1="{dim_x_depth + 5}" y1="{girder_bottom_y}" x2="{girder_x}" y2="{girder_bottom_y}" stroke="black" stroke-width="0.5" stroke-dasharray="2,2"/>')
        svg_parts.append(f'<line x1="{dim_x_depth}" y1="{girder_top_y}" x2="{dim_x_depth}" y2="{girder_bottom_y}" stroke="black" stroke-width="1"/>')
        # Text for girder depth (rotated or positioned next to line)
        depth_text_y = girder_top_y + (scaled_girder_depth / 2)
        svg_parts.append(f'<text x="{dim_x_depth - 7}" y="{depth_text_y}" text-anchor="end" dominant-baseline="middle" class="dim_text">Depth: {girder_depth:.2f} m</text>')
        # Arrows for depth dimension
        svg_parts.append(f'<polygon points="{dim_x_depth},{girder_top_y} {dim_x_depth-3},{girder_top_y+5} {dim_x_depth+3},{girder_top_y+5}" fill="black"/>')
        svg_parts.append(f'<polygon points="{dim_x_depth},{girder_bottom_y} {dim_x_depth-3},{girder_bottom_y-5} {dim_x_depth+3},{girder_bottom_y-5}" fill="black"/>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def generate_girder_section(self, design_data: dict) -> str:
        """
        Generates a very basic SVG cross-section of a girder.
        """
        girder_type = design_data.get("main_girder", {}).get("type", "Generic Girder")
        girder_depth = design_data.get("main_girder", {}).get("depth_m", 2.0)
        bridge_width = design_data.get("bridge_width", 10.0) # This is overall bridge width

        # Assume girder width is a fraction of bridge width or a standard value
        # This is a simplification. A real bridge has multiple girders or a deck slab.
        # For a single representative girder:
        girder_flange_width = bridge_width / 4 if "I-Girder" in girder_type else bridge_width / 2 # Simplified
        if girder_flange_width < 0.5: girder_flange_width = 0.5 # min width
        if girder_flange_width > 3.0 and "I-Girder" in girder_type : girder_flange_width = 3.0 # max width for typical I-girder representation

        web_thickness = girder_flange_width * 0.15
        flange_thickness = girder_depth * 0.1

        padding = 30
        svg_width = 300
        svg_height = 250

        # Scale to fit
        max_dim = max(girder_depth, girder_flange_width)
        scale_factor = min((svg_width - 2 * padding) / girder_flange_width if girder_flange_width > 0 else 1,
                           (svg_height - 2 * padding) / girder_depth if girder_depth > 0 else 1)

        s_depth = girder_depth * scale_factor
        s_flange_width = girder_flange_width * scale_factor
        s_web_thickness = web_thickness * scale_factor
        s_flange_thickness = flange_thickness * scale_factor

        center_x = svg_width / 2
        center_y = svg_height / 2

        svg_parts = [
            f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #f9f9f9; border: 1px solid #ccc;">',
            '<style>.dim_text { font-size: 10px; fill: #333; } .title_text { font-size: 14px; font-weight: bold; fill: #003366; }</style>',
            f'<text x="{svg_width/2}" y="20" text-anchor="middle" class="title_text">Girder Section: {girder_type}</text>'
        ]

        if "I-Girder" in girder_type:
            # Top flange
            svg_parts.append(f'<rect x="{center_x - s_flange_width/2}" y="{center_y - s_depth/2}" width="{s_flange_width}" height="{s_flange_thickness}" fill="#cceeff" stroke="#555"/>')
            # Web
            svg_parts.append(f'<rect x="{center_x - s_web_thickness/2}" y="{center_y - s_depth/2 + s_flange_thickness}" width="{s_web_thickness}" height="{s_depth - 2*s_flange_thickness}" fill="#cceeff" stroke="#555"/>')
            # Bottom flange
            svg_parts.append(f'<rect x="{center_x - s_flange_width/2}" y="{center_y + s_depth/2 - s_flange_thickness}" width="{s_flange_width}" height="{s_flange_thickness}" fill="#cceeff" stroke="#555"/>')
        elif "Box Girder" in girder_type: # Simple box
             svg_parts.append(f'<rect x="{center_x - s_flange_width/2}" y="{center_y - s_depth/2}" width="{s_flange_width}" height="{s_depth}" fill="#ddeeff" stroke="#555" stroke-width="1"/>')
             # Could add inner lines for wall thickness if desired
        else: # Generic Rectangular Girder
            svg_parts.append(f'<rect x="{center_x - s_flange_width/2}" y="{center_y - s_depth/2}" width="{s_flange_width}" height="{s_depth}" fill="#ddeeff" stroke="#555"/>')

        # Dimensions (simplified)
        # Depth
        svg_parts.append(f'<line x1="{center_x + s_flange_width/2 + 5}" y1="{center_y - s_depth/2}" x2="{center_x + s_flange_width/2 + 5}" y2="{center_y + s_depth/2}" stroke="black" stroke-width="0.5"/>')
        svg_parts.append(f'<text x="{center_x + s_flange_width/2 + 8}" y="{center_y}" dominant-baseline="middle" class="dim_text">{girder_depth:.2f}m</text>')
        # Width
        svg_parts.append(f'<line x1="{center_x - s_flange_width/2}" y1="{center_y + s_depth/2 + 5}" x2="{center_x + s_flange_width/2}" y2="{center_y + s_depth/2 + 5}" stroke="black" stroke-width="0.5"/>')
        svg_parts.append(f'<text x="{center_x}" y="{center_y + s_depth/2 + 15}" text-anchor="middle" class="dim_text">{girder_flange_width:.2f}m</text>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    # generate_pier_drawing and add_dimensions can be implemented later if needed
    # For now, focusing on elevation and a basic section.
    # def generate_pier_drawing(self, pier_data: dict) -> str:
    #     # 生成桥墩图纸SVG
    #     return f"<svg width='500' height='700'><text x='10' y='20'>Pier Drawing: {pier_data.get('id', 'N/A')}</text></svg>"

    # def add_dimensions(self, svg_content: str, dimensions: list) -> str:
    #     # 添加尺寸标注
    #     # This is a simplified placeholder. Real implementation would parse and modify SVG.
    #     dimension_svg = "".join([f"<text x='{d.get('x', 0)}' y='{d.get('y', 0)}'>{d.get('text', '')}</text>" for d in dimensions])
    #     return svg_content.replace("</svg>", f"{dimension_svg}</svg>")

if __name__ == '__main__':
    gen = SVGGenerator()

    # Test case 1: Simple Beam Bridge
    design1 = {
        "span_lengths": [60.0],
        "main_girder": {"depth_m": 3.0, "type": "Concrete Beam"},
        "bridge_type": "Simple Beam Bridge",
        "bridge_width": 12.0
    }
    svg_elevation1 = gen.generate_bridge_elevation(design1)
    with open("test_elevation1.svg", "w") as f:
        f.write(svg_elevation1)
    print("Generated test_elevation1.svg")

    svg_section1 = gen.generate_girder_section(design1)
    with open("test_section1.svg", "w") as f:
        f.write(svg_section1)
    print("Generated test_section1.svg")

    # Test case 2: Prestressed Concrete I-Girder
    design2 = {
        "span_lengths": [120.0],
        "main_girder": {"depth_m": 5.5, "type": "Prestressed Concrete I-Girder"},
        "bridge_type": "Prestressed Concrete Continuous Girder",
        "bridge_width": 15.0
    }
    svg_elevation2 = gen.generate_bridge_elevation(design2)
    with open("test_elevation2.svg", "w") as f:
        f.write(svg_elevation2)
    print("Generated test_elevation2.svg")

    svg_section2 = gen.generate_girder_section(design2) # Will use I-Girder specific logic
    with open("test_section2.svg", "w") as f:
        f.write(svg_section2)
    print("Generated test_section2.svg")

    # Test case 3: Short span
    design3 = {
        "span_lengths": [20.0],
        "main_girder": {"depth_m": 1.0, "type": "Steel I-Girder"},
        "bridge_type": "Steel Girder Bridge",
        "bridge_width": 8.0
    }
    svg_elevation3 = gen.generate_bridge_elevation(design3)
    with open("test_elevation3.svg", "w") as f:
        f.write(svg_elevation3)
    print("Generated test_elevation3.svg")

    svg_section3 = gen.generate_girder_section(design3)
    with open("test_section3.svg", "w") as f:
        f.write(svg_section3)
    print("Generated test_section3.svg")
