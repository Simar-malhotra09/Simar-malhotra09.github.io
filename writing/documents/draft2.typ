== Introduction
Metallic and oxide nanoparticles play a central role in catalysis, energy storage, biomedicine, and advanced materials, where functional properties depend sensitively on particle size, shape, and poly dispersity. Quantitative characterization of these morphological parameters is essential for process optimization and for establishing reproducible structure–property relationships. Among available techniques, transmission electron microscopy (TEM) and scanning TEM (STEM) remain the most widely used methods for direct imaging at sub-nanometer resolution, providing the spatial detail necessary for single-particle measurement [refs].

Despite the maturity of TEM as an imaging modality, the downstream analysis step of extracting quantitative morphological data from micrographs,  remains largely manual. The standard workflow in most laboratories relies on general-purpose tools such as ImageJ/Fiji [ref], where researchers trace particle boundaries by hand and record measurements one particle at a time. For the statistically meaningful sample sizes of hundreds to thousands of particles typically needed,  this process can consume hours per micrograph. In practice, the annotation cost constrains the number of particles characterized: many studies report distributions over smaller populations than would be desirable simply because the manual effort is prohibitive. This bottleneck is not a limitation of the imaging instrument but of the analysis software available to researchers.

Deep learning has substantially improved automated segmentation of microscopy images. Convolutional neural networks and, more recently, prompt-able foundation models such as the Segment Anything Model (SAM) [ref] have demonstrated strong performance on particle detection and instance segmentation tasks [refs]. Two-stage pipelines that pair an object detector with a segmentation model have proven particularly effective for nanoparticle analysis [Genc et al.]. However, the practical impact of these advances on routine laboratory workflows has been limited by several factors. Most published methods exist as research code validated on curated datasets rather than as distributable software, requiring users to configure Python environments, manage GPU dependencies, and adapt scripts to their specific imaging conditions. Models trained on particular particle morphologies may fail silently on novel chemistries, overlapping structures, or imaging artifacts common in practice [ref]. And purely automated pipelines typically offer no mechanism for researchers to inspect and correct individual measurements before incorporating them into results; this makes it harder for the quantitative accuracy to be defensible.

Classical image analysis techniques, particularly pixel classification with random forests, occupy a complementary niche. These methods require no pre-trained weights, construct their training signal interactively from the image under analysis, and generalize well to unfamiliar contrast conditions [Weka, LABKIT]. Their principal limitation is in instance-level discrimination: a pixel classifier can separate foreground from background effectively but cannot, on its own, resolve individual particles in a dense or overlapping field. Recent tools such as LABKIT [Arzt et al.] have demonstrated that combining classical pixel classification with modern interface design can produce accessible and practical workflows for biological image analysis. An analogous integration for quantitative materials microscopy, which couples deep learning instance segmentation with classical recovery of missed detections, interactive refinement, and calibrated measurement, has not been realized in an end-user tool.

We present a desktop application for automated nanoparticle analysis from TEM images that addresses this gap. The system combines a two-stage deep learning pipeline, consisting of YOLOv8 for object detection and SAM for pixel-accurate instance segmentation [this is Adra Genc et al exact model/weights], with a random forest pixel classifier that identifies particles missed by the primary detector and converts them into segmentation prompts. All outputs are exposed through an interactive refinement interface in which researchers can correct, split, merge, and re-segment individual masks before export. Per-particle morphology statistics, including Feret diameter, area, aspect ratio, circularity, and solidity, are computed in calibrated physical units derived from automatic scale bar detection and are recomputed after every edit, ensuring that exported measurements always reflect the current segmentation state. The entire workflow is packaged as a standalone desktop application that requires no programming knowledge, cloud infrastructure, or dedicated GPU hardware and operates entirely offline. In a comparison against manual polygon annotation on a representative micrograph, the platform reproduced the ground-truth size distribution to within 1% of the mean Feret diameter while reducing total analysis time, including interactive refinement, from 48 minutes to under two minutes.

== Benchmarking against manual straight-line annotation

To evaluate our platform against an established manual workflow, we compared
particle size measurements obtained from four independent sources: manual
polygon annotation (ground truth), the Fiji straight-line tool, the
platform's initial automated segmentation, and the platform's output after
interactive refinement.

=== Dataset

Figure 1 shows the source micrograph used for this comparison. The imaged
particles are approximately spherical, with an aspect ratio close to unity
for the ~30 particles summarized in Table 1 and are largely isolated and
homogeneous in appearance. These properties make the field a tractable
target for a range of segmentation approaches while still spanning the full
size range present in the sample.

=== Annotation protocols

Ground truth was established by manually annotating every visible particle
as a closed polygon, yielding $n = 277$ instances. For the manual baseline,
Fiji's straight-line tool was used to draw a line between the two most
distant visible points of each particle; because the particles are
approximately spherical, this line length serves as a direct proxy for
particle diameter. This was carried out for $n = 50$ particles, reflecting
the time cost of manual, line-by-line annotation.

The same micrograph was then processed with our platform. The initial,
unedited segmentation yielded $n = 271$ particles. We then applied the
platform's interactive refinement module to correct residual segmentation
errors, increasing the count to $n = 275$ particles.

For all four sources we computed a single comparable length metric: the
maximum caliper (Feret) diameter, defined as the greatest pairwise distance
between vertices of each particle's convex hull. For the ground truth and
platform outputs, this was computed directly from the annotated or
segmented polygons; for Fiji, the manually drawn line length was used
directly, as it is itself a caliper measurement.


#figure(
  grid(
    columns: 2,
    gutter: 1em,
    image("draft2/image.jpg", width: 100%),
  ),
  caption: [
    Source micrograph and particle-level statistics. Representative
    micrograph used for the comparison.
  ],
) <fig:setup>

\ 

  #figure(
    table(
      columns: 4,
      align: (center, right, right, right),
      stroke: (x, y) => if y == 0 or y == 1 { (top: 0.8pt) } else { none },
      table.header(
        [*Particle*], [*Longitudinal (px)*], [*Latitudinal (px)*], [*Aspect ratio*],
      ),
      [1],  [25.020], [23.022], [1.087],
      [2],  [23.087], [20.224], [1.142],
      [3],  [22.023], [21.024], [1.048],
      [4],  [22.204], [25.020], [1.127],
      [5],  [20.000], [20.025], [1.001],
      [6],  [23.195], [26.019], [1.122],
      [7],  [21.000], [26.077], [1.242],
      [8],  [22.000], [23.022], [1.046],
      [9],  [21.213], [22.136], [1.044],
      [10], [26.019], [25.318], [1.028],
      table.hline(stroke: 0.8pt),
    ),
    caption: [
      Longitudinal and latitudinal caliper lengths for $n = 10$ ground-truth
      particles, measured manually in Fiji. Aspect ratio is defined as the
      ratio of the larger to the smaller of the two measurements per particle
      (mean = 1.089, maximum deviation from unity = 0.242), consistent with
      the approximately spherical morphology of the imaged particles.
    ],
  ) <fig:aspect-ratio>


=== Results

Figure 2 shows the resulting length distributions for all four methods as a
kernel density estimate, an empirical cumulative distribution function, and
a box plot with jittered points. The platform's initial output
(mean = 26.98 px, median = 26.57 px, $n = 271$) closely tracks the ground
truth distribution (mean = 26.63 px, median = 26.63 px, $n = 277$), and
refinement brings the distribution marginally closer still
(mean = 26.87 px, median = 26.57 px, $n = 275$). The Fiji manual
measurements (mean = 23.93 px, median = 24.58 px, $n = 50$) are shifted
toward smaller values and span a narrower range, consistent with a small,
manually selected subsample rather than a full-population measurement.

Annotation time differed by more than two orders of magnitude across
methods. Manual polygon ground truth required 48 min for 277 particles, the
Fiji line-tool baseline required 3 min for 50 particles, and the platform
produced its initial segmentation in 6.11 s, with interactive refinement
adding a further 97 s ($n = 275$ after refinement, 103.11 s total). Despite
this reduction in annotation time, the platform's size distribution remained
closely aligned with the manually annotated ground truth.

The results are summarized in Table 2. 
  

#figure(
  image("draft2/length_distributions.png", width: 100%),
  caption: [
    Particle length / diameter distributions across all four annotation
    methods -- ground truth, Fiji manual straight-line, initial platform
    segmentation, and platform output after refinement -- shown as (left) a
    kernel density estimate, (middle) an empirical cumulative distribution
    function, and (right) a box plot with jittered points. Legend entries
    report annotation time and sample size for each method.
  ],
) <fig:length>

#figure(
    table(
      columns: 6,
      align: (left, center, right, right, right, right),
      stroke: (x, y) => if y == 0 or y == 1 { (top: 0.8pt) } else { none },
      table.header(
        [*Method*], [*n*], [*Annotation time*], [*Mean (px)*], [*Median (px)*], [*Std. dev. (px)*],
      ),
      [Ground truth (manual polygon)], [277], [48 min],        [26.63], [26.63], [2.21],
      [Fiji (manual straight-line)],   [50],  [3 min],         [23.93], [24.58], [2.76],
      [Ours -- initial segmentation],  [271], [6.11 s],        [26.98], [26.57], [3.79],
      [Ours -- after refinement],      [275], [103.11 s],      [26.87], [26.57], [3.47],
      table.hline(stroke: 0.8pt),
    ),
    caption: [
      Summary of particle length / diameter measurements and annotation time
      across the four methods compared in Fig. 2. Length is the maximum
      caliper (Feret) diameter for the ground truth and platform outputs, and
      the manually drawn line length for Fiji. Annotation time is wall-clock
      time to produce each result set; the platform's refinement step is
      reported cumulatively (initial segmentation + refinement).
    ],
  ) <tab:results-summary>

