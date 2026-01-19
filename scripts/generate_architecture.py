#!/usr/bin/env python
"""Generate the corrected architecture diagram for the paper."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Initialize Figure
fig, ax = plt.subplots(1, 1, figsize=(16, 11))
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis('off')

# --- Configuration ---
# Main vertical axis center for the Agent/Tool stack
CENTER_X = 7.0 
# Width of the main container layers
LAYER_WIDTH = 10.4
# Starting X for the main containers
LAYER_START_X = CENTER_X - (LAYER_WIDTH / 2)

colors = {
    'user': '#4A90D9',
    'agent': '#7B68EE', 
    'tool': '#50C878',
    'flow': '#FF8C42',
    'base': '#708090',
    'text': '#1a1a2e',
    'arrow': '#555555'
}

# --- Helper Function ---
def draw_fancy_box(ax, x, y, width, height, color, label, sublabel=None, 
                   fontsize=10, fontweight='bold', alpha=0.85, 
                   textcolor='white', boxstyle='round,pad=0.03'):
    """Draws a box and centers text inside it."""
    box = FancyBboxPatch((x, y), width, height, boxstyle=boxstyle,
                          facecolor=color, edgecolor='white', linewidth=1.5, alpha=alpha)
    ax.add_patch(box)
    
    center_x = x + (width / 2)
    center_y = y + (height / 2)
    
    if sublabel:
        # If there is a sublabel, shift main label up slightly
        ax.text(center_x, center_y + 0.15, label, fontsize=fontsize, 
                fontweight=fontweight, ha='center', va='center', color=textcolor)
        ax.text(center_x, center_y - 0.25, sublabel, fontsize=fontsize-2, 
                ha='center', va='center', color=textcolor, linespacing=1.1)
    else:
        ax.text(center_x, center_y, label, fontsize=fontsize, 
                fontweight=fontweight, ha='center', va='center', color=textcolor)
    return box

# --- Title ---
ax.text(CENTER_X, 10.5, 'OpenAgent Architecture', fontsize=20, fontweight='bold', 
        ha='center', va='center', color=colors['text'])

# --- User Input Layer ---
# Width 5, centered at CENTER_X
user_w = 5.0
user_x = CENTER_X - (user_w / 2)
draw_fancy_box(ax, user_x, 9.3, user_w, 0.8, colors['user'], 'User Input', fontsize=13)

# --- Agent Layer Container ---
agent_layer_box = FancyBboxPatch((LAYER_START_X, 5.0), LAYER_WIDTH, 3.8, boxstyle='round,pad=0.1',
                              facecolor='#f0f0ff', edgecolor=colors['agent'], linewidth=2, alpha=0.3)
ax.add_patch(agent_layer_box)
ax.text(CENTER_X, 8.5, 'Agent Layer', fontsize=12, fontweight='bold', ha='center', va='center', color=colors['agent'])

# --- Individual Agents ---
# 4 Agents, distributed evenly inside the layer
agent_w = 2.4
gap = (LAYER_WIDTH - (4 * agent_w)) / 5  # Calculate gap to fit 4 items
agent_y = 6.8

agents = [
    ('ManusAgent', 'Primary\nOrchestrator'),
    ('PlanningAgent', 'Memory-Enabled\nExecution'),
    ('ReactAgent', 'Thought-Action\nObservation'),
    ('SWEAgent', 'Code-Aware\nWorkflow')
]

agent_centers_x = [] # Store for arrows

current_x = LAYER_START_X + gap
for name, desc in agents:
    draw_fancy_box(ax, current_x, agent_y, agent_w, 1.3, colors['agent'], name, desc)
    agent_centers_x.append(current_x + agent_w/2)
    current_x += agent_w + gap

# --- BaseAgent ---
base_w = 5.0
base_x = CENTER_X - (base_w / 2)
draw_fancy_box(ax, base_x, 5.3, base_w, 0.7, colors['base'], 'BaseAgent (Abstract)', fontsize=11)

# --- Inheritance Arrows ---
# Connect bottom of each agent to top of BaseAgent
for ac_x in agent_centers_x:
    ax.annotate('', xy=(CENTER_X, 6.0), xytext=(ac_x, 6.8),
                arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=1.2, ls='--'))

# --- Tool Layer Container ---
tool_layer_box = FancyBboxPatch((LAYER_START_X, 1.0), LAYER_WIDTH, 3.5, boxstyle='round,pad=0.1',
                             facecolor='#f0fff0', edgecolor=colors['tool'], linewidth=2, alpha=0.3)
ax.add_patch(tool_layer_box)
ax.text(CENTER_X, 4.15, 'Tool Layer', fontsize=12, fontweight='bold', ha='center', va='center', color=colors['tool'])

# --- Tools Row 1 ---
# 5 Tools
tool_w1 = 1.9
gap1 = (LAYER_WIDTH - (5 * tool_w1)) / 6
current_x = LAYER_START_X + gap1
tool_y1 = 3.0

tools_row1 = ['PDFGenerator', 'MarkdownGen', 'CodeGenerator', 'Firecrawl', 'Bash/Py']

for name in tools_row1:
    draw_fancy_box(ax, current_x, tool_y1, tool_w1, 0.75, colors['tool'], name, fontsize=9)
    current_x += tool_w1 + gap1

# --- Tools Row 2 ---
# 3 Tools
tool_w2 = 2.2
gap2 = (LAYER_WIDTH - (3 * tool_w2)) / 4
current_x = LAYER_START_X + gap2
tool_y2 = 2.0

tools_row2 = ['FileSaver', 'StrReplaceEditor', 'GoogleSearch']

for name in tools_row2:
    draw_fancy_box(ax, current_x, tool_y2, tool_w2, 0.75, colors['tool'], name, fontsize=9, alpha=0.75)
    current_x += tool_w2 + gap2

# --- Tool Registry ---
reg_w = 5.0
reg_x = CENTER_X - (reg_w / 2)
draw_fancy_box(ax, reg_x, 1.2, reg_w, 0.6, colors['base'], 'ToolRegistry (Singleton)', fontsize=10)

# --- Flow Layer ---
# Placed to the right of the main stack
flow_x = LAYER_START_X + LAYER_WIDTH + 0.8  # Start 0.8 units right of the agent layer
draw_fancy_box(ax, flow_x, 5.5, 2.2, 2.8, colors['flow'], 'Flow', 'Layer\n(Orchestration)', 
               fontsize=12, alpha=0.85, boxstyle='round,pad=0.05')

# --- Main Data Flow Arrows ---

# User -> Agent Layer (Vertical Center)
ax.annotate('', xy=(CENTER_X, 8.5), xytext=(CENTER_X, 9.3),
            arrowprops=dict(arrowstyle='->', color=colors['arrow'], lw=2))

# Agent Layer <-> Tool Layer (Vertical Center)
ax.annotate('', xy=(CENTER_X, 4.5), xytext=(CENTER_X, 5.25),
            arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=2))

# Agent Layer <-> Flow Layer (Horizontal)
# From right edge of Agent Layer Box to Left edge of Flow Box
agent_box_right = LAYER_START_X + LAYER_WIDTH
flow_box_left = flow_x
arrow_y = 6.9

ax.annotate('', xy=(agent_box_right + 0.1, arrow_y), xytext=(flow_box_left - 0.1, arrow_y),
            arrowprops=dict(arrowstyle='<->', color=colors['arrow'], lw=1.5))

# --- Legend ---
legend_y = 0.4
legend_items = [
    (colors['agent'], 'Agent'),
    (colors['tool'], 'Tool'),
    (colors['flow'], 'Flow'),
    (colors['base'], 'Abstract/Registry')
]

# Center the legend
total_legend_width = (len(legend_items) * 2.6)
legend_start_x = CENTER_X - (total_legend_width / 2) + 0.5

for i, (color, label) in enumerate(legend_items):
    x = legend_start_x + i * 2.6
    box = FancyBboxPatch((x, legend_y-0.15), 0.4, 0.3, boxstyle='round,pad=0.01',
                          facecolor=color, edgecolor='white', linewidth=1, alpha=0.85)
    ax.add_patch(box)
    ax.text(x+0.6, legend_y, label, fontsize=9, ha='left', va='center', color=colors['text'])

plt.tight_layout()
# bbox_inches='tight' ensures nothing is cut off
plt.savefig('architecture_fixed.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print('Fixed architecture diagram saved.')