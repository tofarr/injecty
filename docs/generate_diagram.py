"""
Generate a visual diagram of the injecty framework architecture.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.path import Path

# Set up the figure with a light background
plt.figure(figsize=(12, 8))
ax = plt.gca()
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.axis('off')

# Define colors
config_color = '#4472C4'  # Blue
context_color = '#70AD47'  # Green
impl_color = '#ED7D31'    # Orange
client_color = '#5B9BD5'  # Light blue
arrow_color = '#404040'   # Dark gray
bg_color = '#F2F2F2'      # Light gray

# Add a light background
ax.add_patch(patches.Rectangle((0, 0), 12, 8, facecolor=bg_color, edgecolor='none', zorder=-1))

# Draw the InjectyContext box
context_rect = patches.Rectangle((4, 4), 4, 2, facecolor=context_color, edgecolor='black', 
                                alpha=0.7, linewidth=1.5, zorder=2)
ax.add_patch(context_rect)
ax.text(6, 5, 'InjectyContext', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
ax.text(6, 4.5, 'Manages implementations', ha='center', va='center', fontsize=10, color='white')

# Draw the Config Modules
config_rect = patches.Rectangle((1, 6), 2, 1.5, facecolor=config_color, edgecolor='black', 
                               alpha=0.7, linewidth=1.5, zorder=2)
ax.add_patch(config_rect)
ax.text(2, 6.75, 'Config Modules', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.text(2, 6.35, 'injecty_config_*', ha='center', va='center', fontsize=9, color='white')

# Draw the Implementations
impl_rect1 = patches.Rectangle((9, 6), 2, 0.8, facecolor=impl_color, edgecolor='black', 
                              alpha=0.7, linewidth=1.5, zorder=2)
impl_rect2 = patches.Rectangle((9, 5), 2, 0.8, facecolor=impl_color, edgecolor='black', 
                              alpha=0.7, linewidth=1.5, zorder=2)
impl_rect3 = patches.Rectangle((9, 4), 2, 0.8, facecolor=impl_color, edgecolor='black', 
                              alpha=0.7, linewidth=1.5, zorder=2)
ax.add_patch(impl_rect1)
ax.add_patch(impl_rect2)
ax.add_patch(impl_rect3)
ax.text(10, 6.4, 'Implementation A', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
ax.text(10, 5.4, 'Implementation B', ha='center', va='center', fontsize=10, fontweight='bold', color='white')
ax.text(10, 4.4, 'Implementation C', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# Draw the Client Application
client_rect = patches.Rectangle((4, 1), 4, 1.5, facecolor=client_color, edgecolor='black', 
                               alpha=0.7, linewidth=1.5, zorder=2)
ax.add_patch(client_rect)
ax.text(6, 1.75, 'Client Application', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.text(6, 1.35, 'Uses injecty to get implementations', ha='center', va='center', fontsize=9, color='white')

# Draw arrows
def draw_arrow(start, end, color=arrow_color, width=0.05, head_width=0.2, head_length=0.2, zorder=1, label=None, label_pos=0.5):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    arrow = patches.FancyArrow(start[0], start[1], dx, dy, width=width, 
                              head_width=head_width, head_length=head_length, 
                              facecolor=color, edgecolor='none', zorder=zorder)
    ax.add_patch(arrow)
    
    if label:
        # Position the label along the arrow
        label_x = start[0] + label_pos * dx
        label_y = start[1] + label_pos * dy
        
        # Add a small white background to the text for better readability
        text = ax.text(label_x, label_y, label, ha='center', va='center', fontsize=9, 
                      fontweight='bold', color='black', zorder=zorder+1)
        text.set_bbox(dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))

# Config modules to Context
draw_arrow((3, 6.75), (4, 5.5), label='configure()', label_pos=0.4)

# Context to Implementations (register)
draw_arrow((8, 5.5), (9, 6.4), label='register_impl()', label_pos=0.5)
draw_arrow((8, 5), (9, 5.4), label='register_impl()', label_pos=0.5)
draw_arrow((8, 4.5), (9, 4.4), label='register_impl()', label_pos=0.5)

# Client to Context
draw_arrow((6, 2.5), (6, 4), label='get_impls()', label_pos=0.4)

# Context to Client (return implementations)
draw_arrow((7, 4), (7, 2.5), label='return impls', label_pos=0.6)

# Add a title
plt.title('Injecty Framework Architecture', fontsize=16, fontweight='bold', pad=20)

# Add a legend
legend_elements = [
    patches.Patch(facecolor=config_color, edgecolor='black', alpha=0.7, label='Config Modules'),
    patches.Patch(facecolor=context_color, edgecolor='black', alpha=0.7, label='InjectyContext'),
    patches.Patch(facecolor=impl_color, edgecolor='black', alpha=0.7, label='Implementations'),
    patches.Patch(facecolor=client_color, edgecolor='black', alpha=0.7, label='Client Application')
]
ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.05), 
         ncol=4, fancybox=True, shadow=True)

# Add explanatory text
explanation = """
Injecty is a dependency injection framework that allows for dynamic discovery and registration of implementations.
1. Config modules (injecty_config_*) are discovered and loaded automatically
2. Each config module registers implementations with the InjectyContext
3. Client applications use the InjectyContext to get implementations of interfaces
4. Implementations are returned based on priority and can be filtered or sorted
"""
plt.figtext(0.5, 0.92, explanation, ha='center', fontsize=10, 
           bbox=dict(facecolor='white', alpha=0.8, edgecolor='lightgray', boxstyle='round,pad=0.5'))

# Ensure the docs directory exists
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)

# Save the diagram
plt.tight_layout(rect=[0, 0.1, 1, 0.9])
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'injecty_architecture.png'), dpi=300, bbox_inches='tight')
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'injecty_architecture.svg'), format='svg', bbox_inches='tight')

print("Diagram generated successfully!")