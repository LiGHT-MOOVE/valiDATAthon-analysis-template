import textwrap
from collections.abc import Sequence

import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D

from analysis.visualization.style import PlotStyle


def style_figure(
    fig,
    title: str,
    style=PlotStyle,
    subtitle: str | None = None,
    caption: str | None = None,
) -> None:
    fig.suptitle(
        f"\n{title}",
        fontsize=style.font_title,
        fontweight="bold",
        # y=0.93,
        x=0.02,
        ha="left",
    )
    if subtitle:
        fig.text(
            0.5,
            0.93,
            subtitle,
            ha="center",
            va="center",
            fontsize=style.font_value,
            color="#505050",
        )
    if caption:
        fig.text(
            0.5,
            0.015,
            textwrap.fill(caption, width=120),
            ha="center",
            va="bottom",
            fontsize=style.font_value,
            color="#666666",
        )
    # fig.subplots_adjust(top=top, bottom=bottom)


def add_figure_legend(
    fig,
    handles: Sequence,
    *,
    title: str | None = None,
    y: float = 0.015,
    ncol: int | None = None,
    style=PlotStyle,
) -> None:

    fig.legend(
        handles=handles,
        title=title,
        loc="lower left",
        bbox_to_anchor=(0.01, y),
        ncol=ncol or min(4, len(handles)),
        frameon=False,
        fontsize=style.font_legend,
        title_fontsize=style.font_legend,
        labelcolor="#666666",
        handlelength=2,
        columnspacing=1.4,
    )


def style_x_axes(
    ax,
    *,
    style=PlotStyle,
    xlim=None,
    xticks=None,
    vertical_center_line=None,
    vertical_line_color="#000000",
    vertical_line_style="-",
    xlabels=None,
):
    """Apply the standard axis style."""

    if xlim is not None:
        ax.set_xlim(*xlim)

    if xticks is not None:
        ax.set_xticks(xticks)

    if vertical_center_line is not None:
        ax.axvline(
            vertical_center_line,
            linestyle=vertical_line_style,
            linewidth=1.5,
            color=vertical_line_color,
        )
    if xlabels is not None:
        ax.set_xticklabels(xlabels, fontsize=style.font_tick)
    sns.despine(
        ax=ax,
        left=True,
        bottom=False,
    )

    ax.grid(
        axis="x",
        linestyle="-",
        alpha=0.4,
        zorder=1,
    )

    # X-axis styling
    ax.spines["bottom"].set_color("#000000")
    ax.spines["bottom"].set_linewidth(1.5)
    ax.tick_params(axis="x", colors="#000000", labelsize=style.font_label)
    ax.xaxis.label.set_color("#000000")
    ax.tick_params(
        axis="y",
        which="both",
        left=False,
        right=False,
        labelcolor="black",
        length=0,
    )
    ax.patch.set_alpha(0)
    ax.set_zorder(2)


def style_y_axes(
    ax,
    *,
    style=PlotStyle,
    ylim=None,
    yticks=None,
    set_horizontal_lines=False,
    ylabels=None,
):
    """Apply the standard axis style."""

    if ylim is not None:
        ax.set_ylim(*ylim)

    if yticks is not None:
        ax.set_yticks(yticks)

    if set_horizontal_lines:
        ax.grid(
            axis="y",
            linestyle="-",
            alpha=0.4,
            zorder=1,
        )
    if ylabels is not None:
        ax.set_yticklabels(
            ylabels,
            color="black",
            fontweight="bold",
            fontsize=style.font_tick,
        )
    ax.set_zorder(2)


def finalize_figure(
    fig,
    *,
    style=PlotStyle,
    title,
    xlabel=None,
    ylabel=None,
    legend_handles=None,
    note=None,
    xlabel_v_position=0.05,
    legend_y=0.015,
    legend_col=None,
):
    """Apply standard figure layout, title, xlabel, and legend."""

    style_figure(
        fig,
        title,
    )

    if xlabel is not None:
        fig.supxlabel(
            xlabel,
            fontsize=style.font_label,
            color="#000000",
        )

    if ylabel is not None:
        fig.supylabel(
            ylabel,
            fontsize=style.font_label,
            color="#444242",
        )

    if legend_handles is not None:
        add_figure_legend(fig, legend_handles, y=legend_y, style=style, ncol=legend_col)

    if note is not None:
        fig.text(
            0.4,
            legend_y,
            note,
            ha="left",
            va="bottom",
            fontsize=style.font_label,
            color="#666666",
        )


###
def handle_model_label_and_category(
    ax,
    models,
    model_categories,
    wrap_model=False,
    style=PlotStyle,
):
    for i, model in enumerate(models):
        tag = model_categories[model]

        model_label = (
            textwrap.fill(
                model,
                width=12,
                break_long_words=True,
                break_on_hyphens=True,
            )
            if wrap_model
            else model
        )

        n_lines = model_label.count("\n") + 1

        ax.text(
            -0.02,
            i + 0.08,
            model_label,
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=style.font_value,
            fontweight="bold",
            color="black",
        )

        if tag:
            category_y = i - 0.13 if n_lines == 1 else i - 0.27
            ax.text(
                -0.02,
                category_y,
                tag.upper(),
                transform=ax.get_yaxis_transform(),
                ha="right",
                va="center",
                fontsize=style.font_value,
                color="#666666",
            )


def add_alternating_rows_sub_figures(
    axes,
    n_rows,
    *,
    style=PlotStyle,
    grey_color="#f7f7f7",
):
    """Add alternating grey row backgrounds to the supplied subplots."""

    for ax in np.asarray(axes, dtype=object).ravel():
        for i in range(1, n_rows, 2):
            ax.axhspan(
                i - 0.5,
                i + 0.5,
                xmin=0,
                xmax=1,
                facecolor=grey_color,
                edgecolor="none",
                zorder=0,
            )


def get_countries_offset(no_countries, space=0.18):
    return np.linspace(
        -space,
        space,
        no_countries,
    )


def minimal_axis(ax, grid_axis: str = "y") -> None:
    ax.set_facecolor("white")
    ax.grid(axis=grid_axis, color="#E4E4E4", linewidth=0.7, zorder=0)
    ax.grid(axis="x" if grid_axis == "y" else "y", visible=False)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def create_country_handles(country_colors):
    return [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=country_colors[country],
            markeredgecolor=country_colors[country],
            markersize=7,
            label=country,
        )
        for country in country_colors
    ]
