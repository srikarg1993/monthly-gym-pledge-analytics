from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


def apply_theme():
    """Central place to control seaborn/mpl style."""
    sns.set_theme(style="darkgrid", palette="muted")
    mpl.rcParams["figure.dpi"] = 150
    plt.rcParams["font.family"] = "Consolas"


def set_title_labels(ax, title: str, xlabel: str = "", ylabel: str = ""):
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9, fontweight="bold")
