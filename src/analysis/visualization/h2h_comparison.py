import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

from analysis.helpers import (
    export_figure,
)
from analysis.visualization.helpers import minimal_axis
from analysis.visualization.style import PlotStyle


def plot_win_loss(
    rankings: pd.DataFrame,
    style: PlotStyle,
    model_categories,
    ax: plt.Axes | None = None,
    add_titles=False,
):
    colors = {
        "win": "#217b3b",
        "tie": "#c7c6c1",
        "loss": "#772b83",
    }

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    # Sort by ranking
    rankings = rankings.sort_values("Rank").copy()

    # Calculate outcome percentages directly from rankings
    total = rankings["Wins"] + rankings["Ties"] + rankings["Losses"]

    rankings["winning_pct"] = rankings["Wins"] / total
    rankings["ties_pct"] = rankings["Ties"] / total
    rankings["loss_pct"] = rankings["Losses"] / total

    models = rankings["Model"].tolist()
    y = np.arange(len(models))
    left = np.zeros(len(models))

    for outcome, column in [
        ("win", "winning_pct"),
        ("tie", "ties_pct"),
        ("loss", "loss_pct"),
    ]:
        values = rankings[column].to_numpy()

        bars = ax.barh(
            y,
            values,
            left=left,
            height=1,
            color=colors[outcome],
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )

        for bar, value in zip(bars, values):
            if value >= 0.05:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{value * 100:.1f}",
                    ha="center",
                    va="center",
                    fontsize=style.font_value,
                    fontweight="bold",
                    color="#303030" if outcome == "tie" else "white",
                )

        left += values

    # Model labels with ranks
    ax.set_yticks(
        y,
        models,
        fontsize=style.font_tick,
        fontweight="bold",
        color="black",
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(len(models) - 0.5, -0.5)

    # Winning percentage column on the right
    ax.text(
        1.02,
        1.02,
        "WINNING %",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=style.font_value,
        fontweight="bold",
        color="#666666",
        clip_on=False,
    )

    for y_pos, winning_pct in zip(y, rankings["Winning Percentage"]):
        ax.text(
            1.02,
            y_pos,
            f"{winning_pct * 100:.1f}",
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=style.font_value,
            fontweight="bold",
            color="black",
        )

    # Model category labels
    for y_pos, model in zip(y, models):
        tag = model_categories[model]

        text = ax.text(
            -0.005,
            y_pos + 0.27,
            tag.upper(),
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=style.font_value,
            color="#666666",
        )
        text.set_in_layout(False)

    if add_titles:
        ax.set_xlabel(
            "Percentage of matchups (%)",
            fontsize=style.font_label,
        )
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.tick_params(axis="x", labelsize=style.font_tick)

        legend_handles = [
            Line2D(
                [],
                [],
                marker="s",
                linestyle="None",
                markersize=7,
                markerfacecolor=colors[outcome],
                markeredgecolor="none",
                label=label,
            )
            for outcome, label in [
                ("win", "Win"),
                ("tie", "Tie"),
                ("loss", "Loss"),
            ]
        ]

        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=3,
            frameon=False,
            fontsize=style.font_legend,
            handlelength=1,
            handletextpad=0.4,
            columnspacing=1.5,
        )
    else:
        ax.tick_params(axis="x", labelbottom=False, labelsize=style.font_tick)
        ax.set_xlabel("")

    minimal_axis(ax, "x")

    return fig


###
def plot_head_to_head(
    matrix: pd.DataFrame,
    style: PlotStyle,
    ax: plt.Axes | None = None,
    add_titles=False,
):
    cmap = LinearSegmentedColormap.from_list(
        "head_to_head",
        ["#772b83", "#ffffff", "#217b3b"],
    )
    cmap.set_bad("#EFEFEF")

    fig = ax.figure

    sns.heatmap(
        matrix,
        mask=matrix.isna(),
        vmin=0,
        vmax=1,
        center=0.5,
        cmap=cmap,
        linewidths=0.7,
        linecolor="white",
        annot=False,
        ax=ax,
        cbar=False,
    )
    # outline the diagonal --
    for i in range(min(matrix.shape)):
        ax.add_patch(
            Rectangle(
                (i, i),
                1,
                1,
                fill=False,
                edgecolor="black",
                linewidth=1.2,
                linestyle="--",
            )
        )

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]

            if pd.notna(value):
                ax.text(
                    j + 0.5,
                    i + 0.5,
                    f"{value:.0%}".replace("%", ""),
                    ha="center",
                    va="center",
                    fontsize=style.font_value,
                    fontweight="bold",
                    color=("white" if value <= 0.20 or value >= 0.80 else "#303030"),
                )
    if add_titles:
        ax.set_xlabel("Opposing comparator", fontsize=style.font_label)
        ax.set_xticklabels(
            ax.get_xticklabels(), rotation=25, ha="right", fontsize=style.font_tick
        )

    else:
        ax.set_xlabel("")
        ax.tick_params(axis="x", labelbottom=False, labelsize=style.font_tick)

    ax.tick_params(axis="y", left=False, labelleft=False, labelsize=style.font_tick)

    ax.tick_params(length=0, labelsize=style.font_tick)
    ax.set_ylabel("")

    return fig


def plot_h2h_comparison_main_figure(
    win_loss: pd.DataFrame,
    h2h_matrix: pd.DataFrame,
    countries,
    models,
    config,
    model_categories,
):
    style = config.style
    fig = plt.figure(figsize=(18, 6 * len(countries)), layout="none")

    n_countries = len(countries)

    # Each country gets a header row followed by a plot row
    grid = fig.add_gridspec(
        2 * n_countries + 1,
        2,
        height_ratios=[0.12, 1] * n_countries + [0.08],
        width_ratios=[1, 1],
        left=0.10,
        right=0.97,
        bottom=0.08,
        top=0.94,
        hspace=0.18,
        wspace=0.18,
    )

    country_axes = []

    for i, country in enumerate(countries):
        header_ax = fig.add_subplot(grid[2 * i, :])
        header_ax.set_axis_off()
        header_ax.text(
            -0.05,
            0.85,
            country,
            transform=header_ax.transAxes,
            fontsize=style.font_title,
            fontweight="bold",
            color=style.country_colors[country],
            ha="left",
            va="center",
        )

        header_ax.plot(
            [-0.05, 1],
            [0.35, 0.35],
            transform=header_ax.transAxes,
            color=style.country_colors[country],
            linewidth=5,
            clip_on=False,
        )

    country_axes.append(
        [
            fig.add_subplot(grid[2 * i + 1, 0]),
            fig.add_subplot(grid[2 * i + 1, 1]),
        ]
    )

    cbar_ax = fig.add_subplot(grid[-1, 1])
    for i, (axes, country) in enumerate(zip(country_axes, countries)):
        win_loss_country = win_loss[win_loss["reviewer_country"] == country]
        h2h_matrix_country = h2h_matrix[h2h_matrix["reviewer_country"] == country]
        # Restore model names as the index
        if "Unnamed: 0" in h2h_matrix_country.columns:
            h2h_matrix_country = h2h_matrix_country.set_index("Unnamed: 0")

        # Remove metadata columns
        h2h_matrix_country = h2h_matrix_country.drop(
            columns=["reviewer_country"],
            errors="ignore",
        )
        plot_win_loss(
            win_loss_country,
            style,
            model_categories,
            ax=axes[0],
            add_titles=i + 1 == len(countries),
        )

        plot_head_to_head(
            h2h_matrix_country, style, ax=axes[1], add_titles=i + 1 == len(countries)
        )

    cbar = fig.colorbar(
        country_axes[-1][1].collections[0],
        cax=cbar_ax,
        orientation="horizontal",
    )

    # Horizontal colorbars use the x-axis formatter
    cbar.ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    cbar.ax.tick_params(
        labelsize=style.font_tick,
        length=0,
    )
    cbar.outline.set_visible(False)

    pos = cbar_ax.get_position()

    cbar_ax.set_position(
        [
            pos.x0,
            pos.y0 - 0.04,
            pos.width,
            pos.height,
        ]
    )

    fig.text(
        0.25,
        0.95,
        "a  Aggregate win/tie/loss record vs all other models",
        ha="center",
        va="top",
        fontsize=style.font_title,
        fontweight="bold",
    )

    fig.text(
        0.75,
        0.95,
        "b  Winning % by pairing",
        ha="center",
        va="top",
        fontsize=style.font_title,
        fontweight="bold",
    )
    export_figure(
        fig,
        "h2h_comparison",
        config,
    )
    plt.close(fig)
