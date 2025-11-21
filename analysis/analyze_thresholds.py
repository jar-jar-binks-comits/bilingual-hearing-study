"""
Threshold Analysis
Analyses gap detection and pitch discrimination thresholds across language conditions.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def load_all_thresholds():
    """
    Load all threshold data from processed directory.
    
    Returns
    -------
    pd.DataFrame
        Combined threshold data from all participants
    """
    threshold_files = list(PROCESSED_DATA_DIR.glob('*_thresholds_*.csv'))
    
    if not threshold_files:
        print(f"No threshold files found in {PROCESSED_DATA_DIR}")
        return None
    
    dfs = []
    for file in threshold_files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(combined)} threshold measurements from {len(threshold_files)} files")
    return combined


def calculate_summary_statistics(df):
    """
    Calculate descriptive statistics by condition and test type.
    
    Parameters
    ----------
    df : pd.DataFrame
        Threshold data
    
    Returns
    -------
    pd.DataFrame
        Summary statistics
    """
    # Group by condition and test_type
    summary = df.groupby(['condition', 'test_type'])['threshold'].agg([
        ('n', 'count'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max')
    ]).reset_index()
    
    # Calculate SEM
    summary['sem'] = summary['std'] / np.sqrt(summary['n'])
    
    return summary


def calculate_effect_sizes(df):
    """
    Calculate Cohen's d for bilingual vs monolingual conditions.
    
    Parameters
    ----------
    df : pd.DataFrame
        Threshold data
    
    Returns
    -------
    dict
        Effect sizes for each test type
    """
    results = {}
    
    for test_type in ['gap', 'pitch']:
        test_data = df[df['test_type'] == test_type]
        
        # Get bilingual and monolingual (English + German) thresholds
        bilingual = test_data[test_data['condition'] == 'bilingual']['threshold'].values
        english = test_data[test_data['condition'] == 'english']['threshold'].values
        german = test_data[test_data['condition'] == 'german']['threshold'].values
        monolingual = np.concatenate([english, german])
        
        if len(bilingual) > 0 and len(monolingual) > 0:
            # Cohen's d
            mean_diff = np.mean(bilingual) - np.mean(monolingual)
            pooled_std = np.sqrt((np.var(bilingual) + np.var(monolingual)) / 2)
            cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
            
            results[test_type] = {
                'bilingual_mean': np.mean(bilingual),
                'monolingual_mean': np.mean(monolingual),
                'difference': mean_diff,
                'cohens_d': cohens_d
            }
    
    return results


def plot_thresholds(df, output_dir=None):
    """
    Create visualization of thresholds by condition.
    
    Parameters
    ----------
    df : pd.DataFrame
        Threshold data
    output_dir : Path, optional
        Directory to save figures
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'analysis'
    output_dir.mkdir(exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    conditions = ['english', 'german', 'bilingual']
    condition_labels = ['English', 'German', 'Bilingual']
    colors = ['#268bd2', '#859900', '#dc322f']  # Solarized colors
    
    # Gap Detection
    gap_data = df[df['test_type'] == 'gap']
    gap_means = []
    gap_sems = []
    
    for cond in conditions:
        cond_data = gap_data[gap_data['condition'] == cond]['threshold'].values * 1000  # Convert to ms
        gap_means.append(np.mean(cond_data) if len(cond_data) > 0 else 0)
        gap_sems.append(np.std(cond_data) / np.sqrt(len(cond_data)) if len(cond_data) > 0 else 0)
    
    axes[0].bar(condition_labels, gap_means, yerr=gap_sems, 
                color=colors, alpha=0.7, capsize=5)
    axes[0].set_ylabel('Gap Detection Threshold (ms)', fontsize=12)
    axes[0].set_xlabel('Condition', fontsize=12)
    axes[0].set_title('Gap Detection', fontsize=14, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    
    # Pitch Discrimination
    pitch_data = df[df['test_type'] == 'pitch']
    pitch_means = []
    pitch_sems = []
    
    for cond in conditions:
        cond_data = pitch_data[pitch_data['condition'] == cond]['threshold'].values
        pitch_means.append(np.mean(cond_data) if len(cond_data) > 0 else 0)
        pitch_sems.append(np.std(cond_data) / np.sqrt(len(cond_data)) if len(cond_data) > 0 else 0)
    
    axes[1].bar(condition_labels, pitch_means, yerr=pitch_sems,
                color=colors, alpha=0.7, capsize=5)
    axes[1].set_ylabel('Pitch Discrimination Threshold (Hz)', fontsize=12)
    axes[1].set_xlabel('Condition', fontsize=12)
    axes[1].set_title('Pitch Discrimination', fontsize=14, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    output_file = output_dir / 'threshold_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Figure saved to {output_file}")
    
    plt.show()


def generate_report(df):
    """
    Generate text report of results.
    
    Parameters
    ----------
    df : pd.DataFrame
        Threshold data
    
    Returns
    -------
    str
        Formatted report
    """
    report = []
    report.append("="*60)
    report.append("BILINGUAL HEARING STUDY - THRESHOLD ANALYSIS")
    report.append("="*60)
    report.append("")
    
    # Sample info
    n_participants = df['participant_id'].nunique()
    report.append(f"Participants: {n_participants}")
    report.append(f"Total measurements: {len(df)}")
    report.append("")
    
    # Summary statistics
    report.append("-"*60)
    report.append("SUMMARY STATISTICS")
    report.append("-"*60)
    
    summary = calculate_summary_statistics(df)
    
    for test_type in ['gap', 'pitch']:
        test_summary = summary[summary['test_type'] == test_type]
        
        if test_type == 'gap':
            report.append("\nGap Detection Thresholds (milliseconds):")
            multiplier = 1000
        else:
            report.append("\nPitch Discrimination Thresholds (Hz):")
            multiplier = 1
        
        for _, row in test_summary.iterrows():
            report.append(f"  {row['condition'].capitalize()}: "
                         f"M = {row['mean']*multiplier:.2f}, "
                         f"SD = {row['std']*multiplier:.2f}, "
                         f"n = {int(row['n'])}")
    
    # Effect sizes
    report.append("")
    report.append("-"*60)
    report.append("EFFECT SIZES (Bilingual vs Monolingual)")
    report.append("-"*60)
    
    effects = calculate_effect_sizes(df)
    
    for test_type, stats in effects.items():
        if test_type == 'gap':
            report.append(f"\nGap Detection:")
            multiplier = 1000
            unit = "ms"
        else:
            report.append(f"\nPitch Discrimination:")
            multiplier = 1
            unit = "Hz"
        
        report.append(f"  Bilingual mean: {stats['bilingual_mean']*multiplier:.2f} {unit}")
        report.append(f"  Monolingual mean: {stats['monolingual_mean']*multiplier:.2f} {unit}")
        report.append(f"  Difference: {stats['difference']*multiplier:.2f} {unit}")
        report.append(f"  Cohen's d: {stats['cohens_d']:.3f}")
        
        # Interpret effect size
        d = abs(stats['cohens_d'])
        if d < 0.2:
            interpretation = "negligible"
        elif d < 0.5:
            interpretation = "small"
        elif d < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"
        report.append(f"  Interpretation: {interpretation} effect")
    
    report.append("")
    report.append("="*60)
    
    return "\n".join(report)


def main():
    """Main analysis script."""
    print("\n" + "="*60)
    print("BILINGUAL HEARING STUDY - THRESHOLD ANALYSIS")
    print("="*60 + "\n")
    
    # Load data
    df = load_all_thresholds()
    
    if df is None or len(df) == 0:
        print("No data to analyze. Run experiment first.")
        return
    
    # Generate report
    report = generate_report(df)
    print("\n" + report)
    
    # Save report
    output_dir = Path(__file__).parent.parent / 'analysis'
    output_dir.mkdir(exist_ok=True)
    report_file = output_dir / 'threshold_analysis.txt'
    
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\nReport saved to {report_file}")
    
    # Create plots
    plot_thresholds(df, output_dir)
    
    print("\nAnalysis complete.")


if __name__ == '__main__':
    main()