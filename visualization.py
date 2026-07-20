'''
'''

import os
import numpy as np
import pandas as pd
from glob import glob
from scipy.stats import mannwhitneyu
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FormatStrFormatter, MultipleLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import Axes3D

def plot_comparison(
    points1, 
    points2,
    labels,                  
    y_label,             
    title,                   
    y_max,                   
    outdir, 
    outstr              
):

    fig, ax = plt.subplots()

    parts = ax.violinplot([points1, points2], showmeans=True, showmedians=False, showextrema=True)

    # Style violins
    for pc in parts['bodies']:
        pc.set_facecolor('lightblue')
        pc.set_edgecolor('black')
        pc.set_alpha(0.7)

    if 'cmeans' in parts:
        parts['cmeans'].set_color('black')
        parts['cmeans'].set_linewidth(2)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Set y-axis scale and ticks
    ax.set_ylim(0, y_max)
    tick_step = y_max / 10
    ax.yaxis.set_major_locator(FixedLocator(np.arange(0, y_max + tick_step, tick_step)))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    # Mann-Whitney U test and annotation
    stat, p = mannwhitneyu(points1, points2, alternative='two-sided')
    # if p < 0.00001:
    #     p_text = "p < 0.00001"
    # else:
    #     p_text = f"p = {p:.5f}"
    ax.text(1.5, y_max * 0.96, f"Mann-Whitney U {p}", ha='center', va='top')

    outpath = os.path.join(outdir, outstr)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def visualize_basename(
        outdir,
        tomogram, 
        pixel_size_nm,
        plane_color, 
        bf_plane_color, 
        point_color,
        tag, 
        draw_planes=True,
        best_fit=False
):

    """
    Visualise rotated point cloud together with two reference planes and an
    optional best-fit plane.

    Parameters
    ----------
    points : (N,3) array-like, voxel units
    plane1, plane2 : dict {'origin': (3,), 'normal': (3,)}
    best_fit_plane : bool
        If True, compute & plot an SVD best-fit plane through *points*.
    """

    # ------------------------------------------------------------- colors
    COLOR_ORIGINAL = plane_color
    COLOR_BEST_FIT = bf_plane_color
    POINT_COLOR    = point_color
        
    # ------------------------------------------------------------- data prep 

    pts = np.asarray(tomogram.particles) * pixel_size_nm  # convert to nm

    # axes ranges with padding
    xpad = 0.40
    ypad = 0.05
    zpad = 0.40
    xmin, xmax = pts[:, 0].min(), pts[:, 0].max()
    ymin, ymax = pts[:, 1].min(), pts[:, 1].max()
    zmin, zmax = pts[:, 2].min(), pts[:, 2].max()
    xpad = (xmax - xmin) * xpad
    ypad = (ymax - ymin) * ypad
    zpad = (zmax - zmin) * zpad
    xmin, xmax = xmin - xpad, xmax + xpad
    ymin, ymax = ymin - ypad, ymax + ypad
    zmin, zmax = zmin - zpad, zmax + zpad
    
    # axes spacing for plotting
    xspace = 200
    yspace = 200
    zspace = 20

    # ------------------------------------------------------------- helpers
    def plane_patch_corners(plane):
        o = plane['origin'] * pixel_size_nm
        n = plane['normal'] / np.linalg.norm(plane['normal'])
        nx, ny, nz = n
        if abs(nz) < 1e-8:
            raise ValueError("Plane normal nearly parallel to Z")
        def z_at(x, y):
            return o[2] - (nx * (x - o[0]) + ny * (y - o[1])) / nz
        return np.array([
            [xmin, ymin, z_at(xmin, ymin)],
            [xmin, ymax, z_at(xmin, ymax)],
            [xmax, ymax, z_at(xmax, ymax)],
            [xmax, ymin, z_at(xmax, ymin)]
        ])

    def add_plane(ax, plane_dict, color):
        try:
            corners = plane_patch_corners(plane_dict)
        except ValueError:
            return
        poly = Poly3DCollection([corners], facecolor=color,
                                alpha=0.80, edgecolor="none")
        ax.add_collection3d(poly)

    def draw_plane_slice(ax, plane, axis0, axis1, color):
        """
        Draw the 2D line where a plane intersects the given view.
        axis0 / axis1 are:
        (0, 2) → XZ view  → slice along constant Y
        (1, 2) → YZ view  → slice along constant X
        """
        print(f"plane origin = {plane['origin']}")
        o = plane['origin'] * pixel_size_nm
        n = plane['normal'] / np.linalg.norm(plane['normal'])
        nx, ny, nz = n

        if abs(nz) < 1e-8:
            return  # skip vertical planes

        if (axis0, axis1) == (0, 2):  # XZ view
            x1, x2 = ax.get_xlim()
            y0 = o[1]  # slice at the plane's own Y
            z1 = o[2] - (nx * (x1 - o[0]) + ny * (y0 - o[1])) / nz
            z2 = o[2] - (nx * (x2 - o[0]) + ny * (y0 - o[1])) / nz
            ax.plot([x1, x2], [z1, z2], ls="--", lw=2.0, color=color, alpha=0.6)

        elif (axis0, axis1) == (1, 2):  # YZ view
            y1, y2 = ax.get_xlim()
            x0 = o[0]  # slice at the plane's own X
            z1 = o[2] - (nx * (x0 - o[0]) + ny * (y1 - o[1])) / nz
            z2 = o[2] - (nx * (x0 - o[0]) + ny * (y2 - o[1])) / nz
            ax.plot([y1, y2], [z1, z2], ls="--", lw=2.0, color=color, alpha=0.6)

    # ------------------------------------------------------------- figures

    # --- 3-D View (Figure 1)
    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111, projection='3d')
    ax1.view_init(elev=5, azim=130)
    ax1.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
                s=2, color=POINT_COLOR, alpha=0.6)
    if draw_planes: #Whether or not to draw in border planes
        add_plane(ax1, tomogram.plane1, COLOR_ORIGINAL)
        add_plane(ax1, tomogram.plane2, COLOR_ORIGINAL)    
    if best_fit: #Whether or not to draw in bestfit plane
        add_plane(ax1, tomogram.bestfit_plane, COLOR_BEST_FIT)
    ax1.set_xlim(xmin, xmax)
    ax1.set_ylim(ymin, ymax)
    ax1.set_zlim(zmin, zmax)
    ax1.set_xlabel("X (nm)")
    ax1.set_ylabel("Y (nm)")
    ax1.set_zlabel("Z (nm)")
    ax1.set_title(f"{tomogram.name} – 3-D")
    ax1.tick_params(axis='both', direction='in', tickdir='in')
    ax1.xaxis.set_major_locator(MultipleLocator(xspace))
    ax1.yaxis.set_major_locator(MultipleLocator(yspace))
    ax1.zaxis.set_major_locator(MultipleLocator(zspace))

    # --- 2D Views (Figure 2)
    fig2, axs2 = plt.subplots(2, 1, layout='constrained')
    # --- XZ View --- (Figure 2 SubPlot 1)
    axs2[0].scatter(pts[:, 0], pts[:, 2], s=2, color=POINT_COLOR, alpha=0.6)
    axs2[0].set_xlim(0, 800) 
    axs2[0].set_ylim(zmin, zmax)  
    axs2[0].set_xlabel("X (nm)")
    axs2[0].set_ylabel("Z (nm)")
    axs2[0].set_title("XZ View")
    axs2[0].tick_params(tickdir='in')
    axs2[0].yaxis.set_major_locator(MultipleLocator(zspace))

    #draw_plane_slice(axs2[0], tomogram.plane1, 0, 2, COLOR_ORIGINAL)
    #draw_plane_slice(axs2[0], tomogram.plane2, 0, 2, COLOR_ORIGINAL)
    if best_fit:
        draw_plane_slice(axs2[0], tomogram.bestfit_plane, 0, 2, COLOR_BEST_FIT)

    # --- YZ View --- (Figure 2 SubPlot 2)
    axs2[1].scatter(pts[:, 1], pts[:, 2], s=2, color=POINT_COLOR, alpha=0.6)
    axs2[1].set_xlim(0, 800) 
    axs2[1].set_ylim(zmin, zmax) 
    axs2[1].set_xlabel("Y (nm)")
    axs2[1].set_ylabel("Z (nm)")
    axs2[1].set_title("YZ View")
    axs2[1].tick_params(tickdir='in')
    axs2[1].yaxis.set_major_locator(MultipleLocator(zspace))

    #draw_plane_slice(axs2[1], tomogram.plane1, 1, 2, COLOR_ORIGINAL)
    #draw_plane_slice(axs2[1], tomogram.plane2, 1, 2, COLOR_ORIGINAL)
    if best_fit:
        draw_plane_slice(axs2[1], tomogram.bestfit_plane, 1, 2, COLOR_BEST_FIT)

    # save figures
    fig1.tight_layout(pad=4)
    png_file = os.path.join(outdir, f"{tomogram.name}_{tag}_3DView.png")
    svg_file = os.path.join(outdir, f"{tomogram.name}_{tag}_3DView.svg")
    fig1.savefig(png_file, dpi=300)
    fig1.savefig(svg_file)
    plt.close(fig1)

    # fig2.tight_layout(pad=4)
    png_file = os.path.join(outdir, f"{tomogram.name}_{tag}_2DViews.png")
    svg_file = os.path.join(outdir, f"{tomogram.name}_{tag}_2DViews.svg")
    fig2.savefig(png_file, dpi=300)
    fig2.savefig(svg_file)
    plt.close(fig2)