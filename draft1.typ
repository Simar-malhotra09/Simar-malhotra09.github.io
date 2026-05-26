#import "@preview/charged-ieee:0.1.4": ieee

#show: ieee.with(
  title: [TemSeg Overview Draft xx],
  abstract: [
    Quantitative characterization of nanoparticle size and shape distributions from Transmission Electron Microscopy (TEM) images remains a critical bottleneck in materials science workflows. Existing approaches rely on manual annotation on legacy software that trades accuracy for throughput. We present TEMseg, an open-source desktop application that combines deep learning-based instance segmentation with interactive refinement and automated analysis. 

  The application supports multiple domain finetuned models varied across sizes for flexibility and provides a human-in-the-loop workflow where researchers can refine segmentation results through direct contour manipulation, single-click particle splitting, and region-based re-segmentation. Per-particle morphological statistics  are computed from exact pixel masks with automatic physical unit calibration from microscope metadata.  TEMseg ships as a self-contained native application requiring no programming expertise, reducing analysis time from hours of manual work to minutes of interactive review.
  ],
)

= Features

== Image Upload 
The application supports two common image upload mechanisms: users may either click
the image workspace to open the system file picker or drag and drop files directly into the
upload area. Currently supported formats include TIF/TIFF, EMD, JPG/JPEG, PNG, and
NumPy array files.
Where available, metadata embedded within the image file such as pixel size and scale
information is automatically extracted and stored for downstream analysis. Clicking the
application logo clears the current workspace, removes the loaded image, and resets the
workflow state.




== Choosing models
The initial goal of this tool was to provide accessible support for state-of-the-art particle
segmentation models, especially for users without dedicated GPU hardware. At present,
the application provides access to two segmentation pipelines as can be seen in @fig:left-sidebar :


=== YoloSAM by Ardra Genc et al.
#linebreak()
YoloSAM is a dual-model segmentation pipeline that combines YOLOv8 for object
detection with Segment Anything Model (SAM) for dense segmentation. YOLOv8 first
detects regions of interest by generating bounding boxes, which are then passed to SAM to 
generate instance-segmented particle masks. The models were fine-tuned by Genc et al.
on a custom annotated TEM dataset, described in detail in their work. We use their
published YOLOv8 weights together with the upstream SAM ViT-B checkpoint without
modification.
Our contribution focuses on improving runtime efficiency of the original pipeline while
preserving output quality and segmentation accuracy. Three main optimizations were
introduced:

1. _ONNX Runtime acceleration for YOLO inference_
The original PyTorch YOLOv8 model was exported once to ONNX format during
packaging. Inference is then executed through ONNX Runtime, which performs
graph-level optimizations such as operator fusion and constant folding while using
CPU-optimized kernels. On our 31-image CPU benchmark, this reduced YOLO
inference time from $1.52 plus.minus 0.15$s to $1.09 plus.minus 0.15$s (approximately $1.4 times$ faster) without
affecting detection outputs.

2. _Persistent SAM predictor reuse_
In the reference implementation, the SAM checkpoint and predictor are reloaded
for every segmentation call. In our implementation, the predictor is initialized once
at process startup and reused across images and segmentation runs. This removes
repeated checkpoint loading and device transfer overhead, reducing end-to-end
runtime from $7.11 plus.minus 3.84$ s to $6.05 plus.minus 2.59$ s per image.

3. _Caching of SAM image embeddings_
The SAM image encoder, based on a ViT-B backbone, dominates runtime cost.
During interactive workflows, users frequently re-run segmentation on the same
image while adjusting parameters. Instead of recomputing image embeddings each
time, our pipeline caches the encoded image features and reuses them for
subsequent runs. Only the lightweight decoder stage is recomputed. This reduces
repeat-call SAM runtime from $4.48 plus.minus 2.28$s to $1.43 plus.minus 1.70$ s ($3.1 times$ faster), and overall
re-run time from $5.98 plus.minus 2.32$ s to $2.47 plus.minus 1.70$s ($2.4 times$ faster). 

All implementation related improvement are summarized in the @fig:table1 
// #pagebreak()
#figure(
  placement: top,
  scope: "parent",
  caption: [Engineering deltas between the original YoloSAM pipeline and the TemSeg implementation. Numbers from 31 TEM images on CPU (Apple Silicon).],
)[
  #show table: set text(size: 9pt)
  #table(
    columns: (1fr, 1.4fr, 1.6fr),
    inset: 6pt,
    align: (left + horizon, left + top, left + top),
    table.header(
      [*Category*], [*Original (Genc et al.)*], [*TemSeg implementation*],
    ),

    [YOLOv8 inference backend],
    [Detector weights served through a general-purpose deep-learning framework in
     dynamic (eager) execution mode.
     #linebreak()
     #linebreak()

    Measured: $1.52 plus.minus 0.15$ s
   ],
    [Detector weights exported to a static inference graph at packaging time and
     served through a dedicated inference runtime, which applies ahead-of-time
     graph optimisation and hardware-tuned kernels.
     #linebreak()
     #linebreak()
    Measured: $1.09 plus.minus 0.15$ s per
     image, $1.4 times$ faster.],

    [SAM predictor lifecycle],
    [The segmentation model is reloaded from disk and transferred onto the
     compute device on every segmentation call.
     #linebreak()
     #linebreak()
     Measured: $7.11 plus.minus 0.18$s 

   ],
    [The segmentation model is loaded once at process start and reused across
     all subsequent calls; weight loading and device-transfer cost is paid
     exactly once.
     #linebreak()
     #linebreak()
     Measured: $6.05 plus.minus 0.23$ s (removes $approx 1$s end-to-end).],

    [SAM image-embedding cache],
    [No cache. The image encoder is by far the dominant cost of the
     segmentation stage and runs from scratch on every call, including when the
     user re-segments the same image during interactive refinement.
     #linebreak()
     #linebreak()
    Measured: segmentation stage $4.48$s and end-to-end rerun $5.98$s

   ],
    [Encoded image features are returned alongside the segmentation result and
     threaded back into the next call on the same image, bypassing the encoder
     entirely; only the prompt-conditioned mask decoder runs on reruns.
     #linebreak()
     #linebreak()
     Measured: segmentation stage $1.43$s on rerun
     ($3.1 times$); end-to-end  $2.47$s ($2.4 times$).],
  )
]<fig:table1>
#linebreak()
Despite these optimizations, segmentation quality remains effectively unchanged. The
median mask IoU between our implementation and the reference pipeline is $0.98$, while
IoU against manually annotated ground truth is $0.841 plus.minus 0.062$ for our implementation
compared to $0.840 plus.minus 0.064$ for the reference implementation. All benchmarks were
performed on CPU-only Apple Silicon hardware across four ground-truth images and 
twenty-seven additional TEM images. Raw benchmark CSV files, aggregation scripts, and
evaluation harnesses are included in the supplementary materials.


=== MaskRCNN
#linebreak()
We also trained a custom Mask R-CNN model as part of this work. The primary goal was
not to achieve state-of-the-art segmentation accuracy, but rather to demonstrate the
feasibility of a modular “plug-and-play” framework in which different segmentation models
can be swapped dynamically within the application.

The model was trained entirely on a synthetic dataset generated procedurally for this
project. Synthetic TEM-like images were created by approximating backgrounds with
Gaussian noise and generating particle-like structures from simple geometric primitives
such as circles, ellipses, and cylinders. Shape perturbations and standard augmentation
techniques including contrast variation, scaling, rotation, and deformation were then
applied to improve generalization.

Although the resulting model performs substantially worse than YoloSAM in terms of
segmentation quality, it offers significantly lower inference latency and provides a useful
lightweight alternative for rapid experimentation and interactive workflows.

On the same four hand-annotated ground-truth images, the model achieved a mean
runtime of $1.62 plus.minus 0.73$s per image on CPU, approximately $4 times$ faster than the first-call
runtime of YoloSAM. However, segmentation accuracy was both lower and
less stable, with a mask IoU against ground truth of $0.696 plus.minus 0.195$, compared to $0.841 plus.minus
0.062$ for YoloSAM.

Performance degradation was most pronounced on densely populated TEM images
containing large numbers of small, visually similar particles. On the most challenging
benchmark image ($approx 300$ densely packed particles), Mask R-CNN achieved an IoU of $0.39$,
while YoloSAM maintained an IoU of $0.85$. This is consistent with the known limitations of
Mask R-CNN on small, crowded, and near-identical object instances, which are
characteristic of nanoparticle TEM imagery.

Based on these results, YoloSAM is used as the primary segmentation pipeline within the
application, while Mask R-CNN serves as a lightweight secondary option prioritizing
inference speed over segmentation fidelity

#pagebreak()

#figure(
  placement: top,
  scope: "parent",
  grid(
    columns: 2,
    gutter: 12pt,
    [(a) \ #image("./figs/model_outputs_overlayed.png", width: 75%)],
    [(b) \ #image("./figs/ground_truth.png", width: 75%)],
    [(c) \ #image("./figs/org_image.png", width: 75%) ],
    [(d) \ #image("./figs/model_output_rncc.png", width: 75%)],
  ),
  caption: [
    \ (a) Original TEM micrograph. \ (b) Manually annotated ground truths. \
    (c) Segmentation mask using YoloSAM overlayed with colorized instance labels. \
    (d) Segmentation mask using MaskRCNN overlayed with colorized instance labels.
  ],
) <fig:SEG>

== Segmentation
Once an image has been loaded and a segmentation model has been selected, the user may start inference by clicking the Run Segmentation button located in the right sidebar. After processing completes, the generated segmentation masks are automatically overlaid on top of the original image. 

Users may toggle the visibility of these overlays at any time using the Show / Hide Masks control. This allows rapid comparison between the raw image and the model predictions without altering the underlying segmentation results. 

Standard image navigation operations are fully supported during analysis, including zooming and panning across the image canvas. The current zoom level is displayed near the top-right status area, and clicking the zoom percentage resets the viewport back to the default centered view. 

#figure(
  placement: none,
  image("./figs/left_sidebar2.png"),
  caption: [Left sidebar]
) <fig:left-sidebar>


== Refinement Mode 
Although the provided segmentation models achieve strong performance, their outputs are still constrained by the limitations of automated inference and are not always perfect. To address this, the application provides an interactive refinement mode that allows users to correct segmentation masks without restarting the workflow. 

Clicking the Refine Mode button switches the application into an editing interface where all generated masks are converted into editable polygons. Individual polygon vertices can be moved directly to better align masks with particle boundaries. Additional vertices may be inserted by clicking along a polygon edge, allowing users to represent more complex geometries, while double-clicking a vertex removes it. 

Each polygon also contains a movable centroid handle that enables rotation and orientation adjustment. Standard editing shortcuts are supported: pressing Delete or Backspace removes the selected polygon, while Ctrl+Z and Ctrl+Y provide undo and redo functionality. These tools enable efficient correction of common segmentation errors, such as slight over-segmentation or under-segmentation around particle boundaries. 

For larger errors such as severely incorrect masks or completely missed particles, users may duplicate an existing polygon with a similar shape using copy-paste operations (Ctrl+C / Ctrl+V). The duplicated polygon can then be repositioned and refined manually to fit the target particle. This significantly reduces the effort required to annotate missing structures from scratch. 

A particularly common failure case in TEM nanoparticle analysis occurs when adjacent particles appear fused together with weak or indistinguishable boundaries. In these cases, the model may incorrectly segment multiple particles as a single instance. To address this, the application includes a Split Instance mode accessible from the sidebar. In this mode, users place a set of foreground marker points over the desired particle regions. Thesepoints are then passed to Segment Anything Model (SAM) as prompt inputs, allowing the selected particle region to be re-segmented into multiple instances. The resulting masks may then be further refined manually if required. 

Because refinement operations are performed interactively, changes must be explicitly saved using the Save Refinements option in the sidebar. Exiting refinement mode without saving discards all unsaved edits. 

Overall, refinement mode provides a practical balance between automated segmentation and human correction, enabling users to efficiently achieve the level of accuracy required for downstream quantitative analysis.

== Stats Panel  

A statistics sidebar is displayed on the right side of the workspace. When an image is first loaded, the panel presents image metadata including the session ID, image dimensions, file format, and any embedded metadata available from the source file, such as pixel size and physical units. 

After segmentation is completed, the panel is automatically populated with summary statistics derived from the detected particle masks. These include: 

#list(
  [Total particle count],

  [Particle coverage percentage],

  [\*Average equivalent diameter],

  [Average particle area], 

  [Average circularity],

  [Average aspect ratio],

)
\*The equivalent diameter is defined as the diameter of a circle with the same area as the segmented particle.  \ 
#linebreak()
When pixel-to-unit calibration metadata is available (for example nanometers per pixel), all size-related measurements are additionally displayed in physical units. 

The panel also contains a View Details button which opens the full statistics dashboard described in the following section. Beneath the summary metrics, a compact histogram provides a quick overview of the particle size distribution, with particle count on the y-axis and equivalent diameter on the x-axis. This visualization is intended as a lightweight summary, while more detailed and interactive analysis tools are provided in the dashboard view. Mean, median, and diameter range statistics are also displayed alongside the histogram. 

The final section of the panel presents a particle shape distribution summary. Each segmented particle is categorized into a predefined morphological class using heuristic rules derived from geometric descriptors such as aspect ratio, circularity, solidity, and polygon vertex count. Current categories include: 

#table(
  columns: (1.6fr, 3.4fr),
  inset: 8pt,
  stroke: 0.5pt,

  [*Shape Classification*], [*Heuristic Criteria*],

  [Rod],
  [Aspect ratio > 2.5],

  [Spherical],
  [Circularity > 0.90, solidity > 0.95, and aspect ratio < 1.2],

  [Triangular],
  [Solidity > 0.92, circularity > 0.70, and polygon vertex count ≤ 4],

  [Faceted],
  [Solidity > 0.92, circularity > 0.70, and polygon vertex count between 5 and 7],

  [Quasi-spherical],
  [Solidity > 0.92 and circularity > 0.70 with polygon vertex count > 7, or fallback classification],

  [Elongated],
  [Aspect ratio > 1.5 and not classified as rod],

  [Irregular],
  [Solidity < 0.85],
)
#linebreak()
For example, highly elongated particles with large aspect ratios are classified as rods, while particles with high circularity and solidity are classified as spherical. Intermediate or less regular structures are categorized using combinations of these geometric properties. These classifications are intended as lightweight morphological descriptors rather than rigorous crystallographic labels, and primarily serve as a rapid exploratory aid during analysis. 


#figure(
  placement: top,
  image(
    "./figs/stats_panel.png",
    width: 55%,
  ),
  caption: [Stats panel. This shows an overview of the stats computed by re-running YoloSAM on an image stored in emd format \ The time for the inital run was $6.38 plus.minus 0.18$s. Our implementation of YoloSAM reduces re-runs to $1.68$s.  \ The tool automatically extract all metadata stored in the file and in this case converts the stats from pixels into metric units using the pixel size field.]
) <fig:stats-panel>


#linebreak()
== Stats Dashboard

Clicking the _View Details_ button in the statistics panel opens a dedicated dashboard containing detailed quantitative analysis for the current segmentation session. The dashboard is designed to provide both publication-ready statistical summaries and interactive exploratory tools for particle analysis.

The first section expands upon the particle size distribution histogram shown in the sidebar. The y-axis represents particle count, while the x-axis represents the selected measurement metric. Users may dynamically switch between equivalent diameter and particle area. Measurements are grouped into configurable histogram bins representing short numerical ranges into which particles are sorted and counted. Mean, median, and standard deviation values are clearly labeled alongside the visualization.

#linebreak()
#figure(
  placement: top,
  scope: "parent",
  image("./figs/stats_dash_b.png"),
  caption: [Engineering deltas between the original YoloSAM pipeline and the TemSeg implementation. Numbers from 31 TEM images on CPU (Apple Silicon).],
)
<fig:stats-dashboard>

#linebreak()
In addition to the raw histogram, the dashboard overlays a fitted probability distribution curve. This functionality is intended not merely as a visualization aid, but as a statistically meaningful summary of nanoparticle ensemble morphology commonly reported in TEM literature. Each segmented particle contributes an equivalent diameter and area measurement, expressed either in calibrated physical units or in pixels when calibration metadata is unavailable. Once at least $10$ particles are detected, we fit three candidate distributions independently to both diameter and area measurements:

#list(
  [Normal distribution],

  [Lognormal distribution],

  [Weibull distribution],
)

The fitting procedure uses maximum-likelihood parameter estimation implemented through SciPy statistical routines. For each candidate distribution, a Kolmogorov--Smirnov (KS) goodness-of-fit test is performed against the observed particle measurements. The resulting KS $p$-value estimates how plausibly the observed data could have been generated by the fitted distribution. The distribution with the highest $p$-value is selected as the best-fit model and rendered as an overlay on the histogram together with its fitted parameters. If fewer than $10$ particles are available, the fit is marked unreliable and the curve is omitted.

This analysis is valuable for several reasons. First, lognormal particle size distributions are widely reported in nanoparticle and catalysis literature because they naturally arise from multiplicative growth processes such as Ostwald ripening and coalescence. Reporting only a mean and standard deviation is often insufficient, since distributions with identical averages may possess very different shapes and physical interpretations. The fitted distribution parameters therefore provide a compact, publication-ready summary of the nanoparticle ensemble.

Second, the fitting procedure also acts as a diagnostic signal for segmentation quality. Well-prepared nanoparticle samples frequently exhibit approximately lognormal size distributions. Poor fits or unexpectedly shaped distributions may indicate upstream segmentation issues such as merged particles or over-segmentation artifacts. Comparing fit quality across the Normal, Lognormal, and Weibull families can additionally reveal skewed or multimodal populations that may correspond to contamination, heterogeneous synthesis conditions, or region-selection artifacts.

#linebreak()
#figure(
  placement: top,
  scope: "parent",
  image("./figs/stats_dash_a.png"),
  caption: [Engineering deltas between the original YoloSAM pipeline and the TemSeg implementation. Numbers from 31 TEM images on CPU (Apple Silicon).],
)
<fig:stats-dashb>

#linebreak()

The dashboard also presents a particle shape distribution visualization summarizing the morphological categories described previously in the statistics sidebar. Both graphical and numerical summaries are provided. Users may interactively exclude individual shape categories from the graph by clicking the corresponding legend entry, causing the visualization to update dynamically. Percentage contributions for each morphology class are also displayed.

The final section of the dashboard contains a detailed per-particle analysis table. Each row corresponds to an individual segmented particle, while columns include:

#list(
  [Particle ID],

  [Equivalent diameter],

  [Area],

  [Circularity],

  [Aspect ratio],

  [Solidity],

  [Number of polygon vertices],

  [Shape classification],
)

Columns may be sorted in ascending or descending order by clicking the corresponding header, enabling rapid filtering and comparison of particle properties. Selecting a table row automatically returns the user to the workspace and highlights the associated particle within the segmentation overlay. This enables direct correlation between quantitative measurements and visual morphology.

Additionally, clicking a shape-class label highlights all particles belonging to that morphological category simultaneously, enabling rapid visual inspection of grouped particle populations. A _Back to Workspace_ button is provided to return to the main segmentation interface without losing workflow progress or analysis state.

== Export
The application also provides an export interface accessible from the left sidebar, allowing users to save both segmentation outputs and derived analysis results for downstream processing or publication workflows.

Clicking the *Export* button opens an export menu where users may selectively choose which outputs to include. Available export options currently include:

#list(
  [Segmentation masks in PNG or NumPy formats],

  [Refined masks generated through refinement mode in PNG or NumPy formats],

  [Polygon instance contour data exported as JSON],

  [Per-particle statistical measurements exported as CSV],
)

#figure(
  image("./figs/export.png", width: 55%),
  caption: [Export interface. This bundles the selection as a zip file which can be easily downloaded.]

)<fig:export>

The exported CSV table contains the same per-particle measurements displayed in the statistics dashboard, including geometric descriptors and morphology classifications. Polygon contour exports preserve the editable instance geometry for downstream reuse or integration into external analysis pipelines.

Users may select any combination of outputs using checkboxes within the export dialog. The selected files are then bundled automatically into a single compressed ZIP archive, after which the system file explorer prompts the user to choose a save location. This enables rapid transfer of segmentation results, annotations, and quantitative measurements into external workflows without additional manual processing.


== Include / Exclude Regions

In many TEM images, certain regions may not be suitable for quantitative analysis. Common examples include dense particle agglomerations where individual particles cannot be reliably separated, imaging artifacts, contamination regions, or areas with poor contrast. To address this, the application provides interactive include/exclude region controls that allow users to define which parts of the image should participate in segmentation and statistical analysis.

Clicking the *Exclude Regions* button in the left sidebar places the application into exclusion mode. Selecting *Draw Regions* enables an editable canvas overlay where users can draw polygonal regions directly on the image. Regions marked for exclusion are displayed in red. Users may either apply the exclusion mask or discard the edits using the corresponding *Apply* and *Exit* controls.

#figure(
  grid(
    columns: 1,
    gutter: 0pt,

    image("./figs/sync-warnign.png", width: 100%),
    image("./figs/exclude.png", width: 100%),
  ),

  caption: [
    The selected regions are excluded for segmentation by zeroing out the pixels.
    The red color signifies exclusion, whereas the isolate feature uses green polygons.
    The status bar displays a synchronization warning indicating that the live image regions are not in sync with the current segmentation output.
  ]
) <fig:exclude>

Internally, excluded regions are masked out by zeroing the corresponding image pixels. Because this modifies the effective analysis image, the status bar warns the user whenever the currently displayed segmentation becomes out-of-sync with the active image state. In these cases, segmentation must be re-run to ensure consistency between the image and detected particle masks.

The application also supports the complementary _Isolate Regions_ mode. Instead of excluding selected areas, isolation mode retains only the selected regions and discards the remainder of the image. Included regions are displayed in green to distinguish them from exclusion masks. A _Clear Regions_ option removes all include/exclude selections and restores the original unmodified image.


These tools are particularly useful for restricting analysis to regions of interest, removing problematic areas from statistical measurements, and improving segmentation reliability on challenging TEM datasets.

== Ground Truth Comparison

The application additionally supports direct comparison between segmentation outputs and user-provided ground truth annotations. A dedicated upload option in the left sidebar allows users to load ground truth masks for the currently active image, typically provided as NumPy (.npy) files.

Basic validation checks are performed automatically to minimize accidental mismatches, including verification of image dimensions and compatibility between the uploaded ground truth and the active image. Ground truth masks may be uploaded either before or after segmentation; evaluation metrics are recomputed automatically whenever both are available.

Once loaded, the application computes standard segmentation evaluation metrics between the model prediction and the ground truth mask, including:

#list(
  [Intersection over Union (IoU): computed as the ratio between the intersection and union of predicted and ground-truth mask pixels],

  [Dice Coefficient: computed as twice the overlap area divided by the total number of pixels across both masks],
)


These metrics are displayed directly within the statistics sidebar, allowing rapid quantitative comparison between models and refinement strategies. Because the framework supports dynamic model switching within a unified interface, users can quickly benchmark multiple segmentation pipelines against the same annotated dataset.

A _Show / Hide Ground Truth_ toggle allows users to overlay the ground truth masks directly on top of the source image or current model outputs for visual verification alongside the numerical metrics. This enables both qualitative and quantitative evaluation within the same workflow.

== Status Bar

A status bar located at the top of the application continuously provides contextual information about the current workflow state and active operations. Users are encouraged to reference it throughout the segmentation and refinement process.

The status bar reports information such as:

#list(
  [Current application mode],

  [Active segmentation state],

  [Refinement or editing operations],

  [Synchronization warnings],

  [Export or save progress],

  [Runtime messages and errors],
)

After segmentation completes, the status bar additionally displays the total inference runtime formatted to two decimal places in seconds. This provides immediate feedback regarding model performance and processing cost during interactive experimentation.
