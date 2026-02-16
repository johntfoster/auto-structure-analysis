"""PDF report generation service for structural analysis."""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, 
    Paragraph, 
    Spacer, 
    Table, 
    TableStyle,
    PageBreak,
    Image as RLImage
)
from reportlab.pdfgen import canvas as pdf_canvas
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np

from app.models.schemas import StructuralModel, AnalysisResults, Load


def generate_report(
    model: StructuralModel, 
    results: AnalysisResults, 
    loads: list[Load],
    material: str = "steel",
    analysis_id: str = "unknown"
) -> bytes:
    """
    Generate a comprehensive PDF report of the structural analysis.
    
    Args:
        model: Structural model
        results: Analysis results
        loads: Applied loads
        material: Material used in analysis
        analysis_id: Unique identifier for the analysis
        
    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=30,
        alignment=1  # Center
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    story.append(Paragraph("Structural Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Report metadata
    metadata = [
        ["Analysis ID:", analysis_id],
        ["Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Material:", material.title()],
        ["Structure Type:", "Truss"],
    ]
    metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Safety Summary
    story.append(Paragraph("Safety Summary", heading_style))
    
    safety_color = colors.HexColor('#10B981') if results.safety_status == 'PASS' else \
                   colors.HexColor('#F59E0B') if results.safety_status == 'WARNING' else \
                   colors.HexColor('#EF4444')
    
    safety_data = [
        ["Parameter", "Value", "Status"],
        ["Max Deflection", f"{results.max_deflection:.3f} mm", ""],
        ["Max Stress Ratio", f"{results.max_stress_ratio:.2%}", ""],
        ["Safety Status", results.safety_status, ""],
    ]
    safety_table = Table(safety_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    safety_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 3), (-1, 3), safety_color),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.white),
        ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
    ]))
    story.append(safety_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Model Summary
    story.append(Paragraph("Model Summary", heading_style))
    
    model_data = [
        ["Component", "Count"],
        ["Nodes", str(len(model.nodes))],
        ["Members", str(len(model.members))],
        ["Supports", str(len(model.supports))],
        ["Loads", str(len(loads))],
    ]
    model_table = Table(model_data, colWidths=[2.5*inch, 2*inch])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(model_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Generate structure visualization
    try:
        structure_img = _generate_structure_image(model, results, loads)
        if structure_img:
            story.append(Paragraph("Structure Visualization", heading_style))
            img = RLImage(structure_img, width=6*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
    except Exception as e:
        print(f"Warning: Could not generate structure image: {e}")
    
    # Page break before detailed results
    story.append(PageBreak())
    
    # Member Forces
    story.append(Paragraph("Member Forces", heading_style))
    
    member_data = [["Member ID", "Axial Force (N)", "Stress (MPa)", "Stress Ratio", "Status"]]
    for mf in results.member_forces:
        status = "FAIL" if mf.stress_ratio >= 1.0 else "WARNING" if mf.stress_ratio >= 0.8 else "OK"
        member_data.append([
            mf.member_id,
            f"{mf.axial:.2f}",
            f"{mf.stress:.2f}",
            f"{mf.stress_ratio:.2%}",
            status
        ])
    
    member_table = Table(member_data, colWidths=[1.2*inch, 1.5*inch, 1.3*inch, 1.3*inch, 0.8*inch])
    
    # Build table style dynamically based on stress ratios
    table_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]
    
    # Color-code status column
    for i, mf in enumerate(results.member_forces, start=1):
        if mf.stress_ratio >= 1.0:
            table_style_commands.append(('BACKGROUND', (4, i), (4, i), colors.HexColor('#FEE2E2')))
        elif mf.stress_ratio >= 0.8:
            table_style_commands.append(('BACKGROUND', (4, i), (4, i), colors.HexColor('#FEF3C7')))
    
    member_table.setStyle(TableStyle(table_style_commands))
    story.append(member_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Reactions
    story.append(Paragraph("Support Reactions", heading_style))
    
    reaction_data = [["Node ID", "Rx (N)", "Ry (N)", "Resultant (N)"]]
    for reaction in results.reactions:
        resultant = np.sqrt(reaction.rx**2 + reaction.ry**2)
        reaction_data.append([
            reaction.node_id,
            f"{reaction.rx:.2f}",
            f"{reaction.ry:.2f}",
            f"{resultant:.2f}"
        ])
    
    reaction_table = Table(reaction_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    reaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(reaction_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Applied Loads
    if loads:
        story.append(Paragraph("Applied Loads", heading_style))
        
        load_data = [["Node ID", "Fx (N)", "Fy (N)", "Magnitude (N)"]]
        for load in loads:
            magnitude = np.sqrt(load.fx**2 + load.fy**2)
            load_data.append([
                load.node_id,
                f"{load.fx:.2f}",
                f"{load.fy:.2f}",
                f"{magnitude:.2f}"
            ])
        
        load_table = Table(load_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        load_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(load_table)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def _generate_structure_image(model: StructuralModel, results: AnalysisResults, loads: list[Load]) -> io.BytesIO:
    """Generate a matplotlib image of the structure with color-coded members."""
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get node coordinates
    node_coords = {node.id: (node.x, node.y) for node in model.nodes}
    
    # Get node coordinates with displacements if available
    if results.nodes_with_displacements:
        node_coords_disp = {
            node.id: (node.x + node.displacement_x * 50, node.y + node.displacement_y * 50) 
            for node in results.nodes_with_displacements
        }
    else:
        node_coords_disp = node_coords
    
    # Plot members with color coding based on stress ratio
    for member in model.members:
        start_coord = node_coords.get(member.start_node)
        end_coord = node_coords.get(member.end_node)
        
        if start_coord and end_coord:
            # Find corresponding force data
            force_data = next((f for f in results.member_forces if f.member_id == member.id), None)
            
            # Determine color based on stress ratio
            if force_data:
                if force_data.stress_ratio >= 1.0:
                    color = '#EF4444'  # Red - failure
                elif force_data.stress_ratio >= 0.8:
                    color = '#F59E0B'  # Yellow - warning
                else:
                    color = '#10B981'  # Green - safe
                
                linewidth = 2 + min(force_data.stress_ratio * 3, 5)
            else:
                color = '#6B7280'
                linewidth = 2
            
            ax.plot(
                [start_coord[0], end_coord[0]], 
                [start_coord[1], end_coord[1]], 
                color=color, 
                linewidth=linewidth,
                solid_capstyle='round'
            )
    
    # Plot nodes
    for node in model.nodes:
        coord = node_coords.get(node.id)
        if coord:
            ax.plot(coord[0], coord[1], 'o', color='#1F2937', markersize=8, zorder=5)
            ax.text(coord[0], coord[1] + 10, str(node.id), 
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot supports
    for support in model.supports:
        coord = node_coords.get(support.node_id)
        if coord:
            if support.type == 'pin':
                ax.plot(coord[0], coord[1], '^', color='#059669', markersize=15, zorder=4)
            elif support.type == 'roller':
                ax.plot(coord[0], coord[1], 'v', color='#059669', markersize=15, zorder=4)
            elif support.type == 'fixed':
                ax.plot(coord[0], coord[1], 's', color='#059669', markersize=12, zorder=4)
    
    # Plot loads
    for load in loads:
        coord = node_coords.get(load.node_id)
        if coord and (abs(load.fx) > 0.1 or abs(load.fy) > 0.1):
            arrow_scale = 0.3
            if abs(load.fx) > 0.1:
                ax.arrow(coord[0], coord[1], load.fx * arrow_scale, 0, 
                        head_width=8, head_length=8, fc='#F59E0B', ec='#F59E0B', linewidth=2)
            if abs(load.fy) > 0.1:
                ax.arrow(coord[0], coord[1], 0, load.fy * arrow_scale, 
                        head_width=8, head_length=8, fc='#F59E0B', ec='#F59E0B', linewidth=2)
    
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X (mm)', fontsize=10)
    ax.set_ylabel('Y (mm)', fontsize=10)
    ax.set_title('Structural Model with Stress Analysis', fontsize=12, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#10B981', label='Safe (<80%)'),
        Patch(facecolor='#F59E0B', label='Warning (80-100%)'),
        Patch(facecolor='#EF4444', label='Failure (>100%)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    
    # Save to BytesIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    return img_buffer
