#!/usr/bin/env python3
"""
Create a visual framework diagram for the Alpha Analyzer merge/split system.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_framework_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Color scheme
    pm_color = '#2E86C1'      # Blue
    merge_color = '#28B463'   # Green  
    split_color = '#F39C12'   # Orange
    trader_color = '#E74C3C'  # Red
    data_color = '#8E44AD'    # Purple
    
    # Title
    ax.text(5, 9.5, 'Alpha Analyzer Framework', fontsize=20, fontweight='bold', 
            ha='center', va='center')
    ax.text(5, 9.1, 'Merge/Split Alpha Trading System Analysis', fontsize=14, 
            ha='center', va='center', style='italic')
    
    # === PORTFOLIO MANAGERS LAYER ===
    pm_y = 7.5
    pm_boxes = []
    for i, pm_id in enumerate(['PM_001', 'PM_002', 'PM_003', 'PM_004', 'PM_005']):
        x = 0.5 + i * 1.8
        box = FancyBboxPatch((x, pm_y), 1.5, 0.8, 
                           boxstyle="round,pad=0.05", 
                           facecolor=pm_color, 
                           edgecolor='black', 
                           alpha=0.8)
        ax.add_patch(box)
        ax.text(x + 0.75, pm_y + 0.4, pm_id, fontsize=10, fontweight='bold', 
                ha='center', va='center', color='white')
        ax.text(x + 0.75, pm_y + 0.15, 'Target Positions', fontsize=8, 
                ha='center', va='center', color='white')
        pm_boxes.append((x + 0.75, pm_y))
    
    # PM Layer Label
    ax.text(-0.3, pm_y + 0.4, 'Portfolio\nManagers', fontsize=12, fontweight='bold',
            ha='center', va='center', rotation=90)
    
    # === MERGE SYSTEM ===
    merge_y = 6
    merge_box = FancyBboxPatch((3.5, merge_y), 3, 0.8,
                              boxstyle="round,pad=0.05",
                              facecolor=merge_color,
                              edgecolor='black',
                              alpha=0.8)
    ax.add_patch(merge_box)
    ax.text(5, merge_y + 0.4, 'MERGE SYSTEM', fontsize=12, fontweight='bold',
            ha='center', va='center', color='white')
    ax.text(5, merge_y + 0.15, 'Sum(PM Targets) by Ticker/Time', fontsize=9,
            ha='center', va='center', color='white')
    
    # === SPLIT SYSTEM ===
    split_y = 4.5
    split_box = FancyBboxPatch((3.5, split_y), 3, 0.8,
                              boxstyle="round,pad=0.05", 
                              facecolor=split_color,
                              edgecolor='black',
                              alpha=0.8)
    ax.add_patch(split_box)
    ax.text(5, split_y + 0.4, 'SPLIT SYSTEM', fontsize=12, fontweight='bold',
            ha='center', va='center', color='white')
    ax.text(5, split_y + 0.15, 'Divide Evenly Across All Traders', fontsize=9,
            ha='center', va='center', color='white')
    
    # === TRADERS LAYER ===
    trader_y = 3
    trader_boxes = []
    for i, trader_id in enumerate(['TRADER_001', 'TRADER_002', 'TRADER_003', 'TRADER_004', 'TRADER_005']):
        x = 0.3 + i * 1.8
        box = FancyBboxPatch((x, trader_y), 1.7, 0.8,
                           boxstyle="round,pad=0.05",
                           facecolor=trader_color,
                           edgecolor='black', 
                           alpha=0.8)
        ax.add_patch(box)
        ax.text(x + 0.85, trader_y + 0.4, trader_id, fontsize=9, fontweight='bold',
                ha='center', va='center', color='white')
        ax.text(x + 0.85, trader_y + 0.15, 'Fill Rate: 0.8-0.9', fontsize=8,
                ha='center', va='center', color='white')
        trader_boxes.append((x + 0.85, trader_y))
    
    # Trader Layer Label
    ax.text(-0.3, trader_y + 0.4, 'Traders\n(Execution)', fontsize=12, fontweight='bold',
            ha='center', va='center', rotation=90)
    
    # === DATA LAYER ===
    data_y = 1.2
    data_files = [
        ('InCheckAlphaEv', 'PM Signals'),
        ('MergedAlphaEv', 'Consolidated'),  
        ('SplitAlphaEv', 'Trader Signals'),
        ('SplitCtxEv', 'Actual Positions'),
        ('VposResEv', 'PM VirtPos')
    ]
    
    for i, (file_name, description) in enumerate(data_files):
        x = 0.2 + i * 1.9
        box = FancyBboxPatch((x, data_y), 1.7, 0.7,
                           boxstyle="round,pad=0.05",
                           facecolor=data_color,
                           edgecolor='black',
                           alpha=0.8)
        ax.add_patch(box)
        ax.text(x + 0.85, data_y + 0.45, file_name, fontsize=9, fontweight='bold',
                ha='center', va='center', color='white')
        ax.text(x + 0.85, data_y + 0.25, description, fontsize=8,
                ha='center', va='center', color='white')
        ax.text(x + 0.85, data_y + 0.05, '.csv', fontsize=8,
                ha='center', va='center', color='white', style='italic')
    
    # Data Layer Label
    ax.text(-0.3, data_y + 0.35, 'CSV Data\nFiles', fontsize=12, fontweight='bold',
            ha='center', va='center', rotation=90)
    
    # === ANALYZER COMPONENT ===
    analyzer_x, analyzer_y = 8.2, 0.5
    analyzer_box = FancyBboxPatch((analyzer_x, analyzer_y), 1.5, 2.2,
                                 boxstyle="round,pad=0.05",
                                 facecolor='#34495E',
                                 edgecolor='black',
                                 alpha=0.9)
    ax.add_patch(analyzer_box)
    ax.text(analyzer_x + 0.75, analyzer_y + 1.9, 'ALPHA', fontsize=11, fontweight='bold',
            ha='center', va='center', color='white')
    ax.text(analyzer_x + 0.75, analyzer_y + 1.7, 'ANALYZER', fontsize=11, fontweight='bold',
            ha='center', va='center', color='white')
    
    analyzer_features = [
        'Fill Rate Analysis',
        'System Validation', 
        'Performance Metrics',
        'Visual Reports',
        'Interactive Plots'
    ]
    
    for i, feature in enumerate(analyzer_features):
        ax.text(analyzer_x + 0.75, analyzer_y + 1.3 - i*0.2, f'• {feature}', fontsize=8,
                ha='center', va='center', color='white')
    
    # === ARROWS AND CONNECTIONS ===
    # PM to Merge arrows
    for pm_x, pm_y_pos in pm_boxes:
        arrow = ConnectionPatch((pm_x, pm_y_pos), (5, merge_y + 0.8), 
                              "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              color='black', lw=2, alpha=0.7)
        ax.add_patch(arrow)
    
    # Merge to Split arrow
    arrow = ConnectionPatch((5, merge_y), (5, split_y + 0.8),
                          "data", "data", 
                          arrowstyle="->", shrinkA=5, shrinkB=5,
                          color='black', lw=3, alpha=0.8)
    ax.add_patch(arrow)
    
    # Split to Traders arrows
    for trader_x, trader_y_pos in trader_boxes:
        arrow = ConnectionPatch((5, split_y), (trader_x, trader_y_pos + 0.8),
                              "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5, 
                              color='black', lw=2, alpha=0.7)
        ax.add_patch(arrow)
    
    # Traders to Data arrows (implicit - show data flow)
    for i in range(5):
        trader_x = trader_boxes[i][0]
        data_x = 0.2 + i * 1.9 + 0.85
        arrow = ConnectionPatch((trader_x, trader_y), (data_x, data_y + 0.7),
                              "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              color='black', lw=1, alpha=0.5, linestyle='--')
        ax.add_patch(arrow)
    
    # Data to Analyzer arrow
    arrow = ConnectionPatch((9.2, data_y + 0.35), (analyzer_x, analyzer_y + 1.1),
                          "data", "data",
                          arrowstyle="->", shrinkA=5, shrinkB=5,
                          color='black', lw=3, alpha=0.8)
    ax.add_patch(arrow)
    
    # === FORMULAS AND KEY CONCEPTS ===
    formula_x, formula_y = 0.5, 0.2
    
    formulas = [
        'Key Formulas:',
        'Merged Target = Σ(PM Targets)',
        'Trader Target = Merged ÷ Num Traders', 
        'Fill Rate = Actual Trade ÷ Intended Trade',
        'PM VPos = Σ(Trader Positions)'
    ]
    
    for i, formula in enumerate(formulas):
        weight = 'bold' if i == 0 else 'normal'
        ax.text(formula_x, formula_y - i*0.15, formula, fontsize=10, fontweight=weight,
                ha='left', va='center')
    
    # === LEGEND ===
    legend_elements = [
        (pm_color, 'Portfolio Managers'),
        (merge_color, 'Merge System'),
        (split_color, 'Split System'), 
        (trader_color, 'Traders'),
        (data_color, 'Data Files')
    ]
    
    for i, (color, label) in enumerate(legend_elements):
        y_pos = 5.5 - i*0.3
        rect = patches.Rectangle((0.1, y_pos-0.1), 0.2, 0.2, 
                               facecolor=color, alpha=0.8)
        ax.add_patch(rect)
        ax.text(0.4, y_pos, label, fontsize=10, ha='left', va='center')
    
    # === CHARACTERISTICS BOX ===
    char_box = FancyBboxPatch((0.1, 3.8), 2.2, 1.5,
                             boxstyle="round,pad=0.1",
                             facecolor='lightgray',
                             edgecolor='black',
                             alpha=0.3)
    ax.add_patch(char_box)
    
    characteristics = [
        'System Characteristics:',
        '• PM ticker overlap (80-90%)',
        '• TVR: ±0.1-0.6 target changes', 
        '• Even trader signal distribution',
        '• Fill rates: 0.8-0.9 realistic',
        '• Position consistency validation'
    ]
    
    for i, char in enumerate(characteristics):
        weight = 'bold' if i == 0 else 'normal'
        ax.text(0.2, 5.15 - i*0.2, char, fontsize=9, fontweight=weight,
                ha='left', va='center')
    
    plt.tight_layout()
    plt.savefig('/home/yves/codebase/alpha-analyzer/framework_diagram.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('/tmp/alpha_analyzer_framework.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    
    print("✅ Framework diagram saved to:")
    print("   - framework_diagram.png (project directory)")
    print("   - /tmp/alpha_analyzer_framework.png (temp directory)")
    
    return fig

if __name__ == "__main__":
    create_framework_diagram()
    plt.show()