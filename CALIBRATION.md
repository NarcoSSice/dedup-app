# Calibration: model and threshold choice

## Data

Testing uses the public **UKBench** dataset ([archive.org/details/ukbench](https://archive.org/details/ukbench)). It has 2550 objects, each photographed 4 times from slightly different angles. The first **150 objects (600 photos)** were used.

Why UKBench: different shots of the same object are exactly what the task calls "similar in content, but not duplicates" (like two different photos of the same coin). These are the pairs where a model is most likely to make mistakes.

Three kinds of pairs were built from these photos:

| Pair type | What it is | Count | Expected |
|---|---|---|---|
| **Duplicates** | an original and its edited copy | 150 × 16 = 2400 | score ≥ threshold |
| **Same object, other photo** | two different shots of the same object | 150 × 3 = 450 | score < threshold |
| **Other object** | an original and the closest photo of a different object | 150 | score < threshold |

The 16 edits cover everything the task counts as a duplicate:
- downscale to 50% and 25%;
- JPEG compression at quality 30 and 10;
- 10% and 20% crop, centered and from a corner;
- brightness ±40%;
- contrast ±50%;
- rotation by 5° and 10°;
- horizontal flip;
- watermark;
- a combination: 15% crop + brightness + watermark + JPEG quality 50.

## Models and methodology

SSCD and the models suggested in the task were tested:

| Model | What it is |
|---|---|
| **SSCD** (ResNet50) | a Meta model trained specifically for image copy detection |
| **DINOv2** ViT-S/14 | a general-purpose self-supervised model by Meta |
| **EfficientNet-B0**, **ResNet50**, **ViT-B/16** | ImageNet classifiers with the classification head removed |
| **CLIP** ViT-B/32 | an OpenAI model that matches images with text |

How the testing was done:
- every image goes through the same processing as in the service: decoding, squashing to 224×224, normalization, a unit-length vector;
- the similarity of a pair is the cosine similarity of the vectors, i.e. the same `score` the API returns;
- for each model, thresholds from 0.30 to 0.99 were tried, picking the one with the best balance of "share of duplicates found minus share of false matches";
- **AUC** is reported separately: the probability that a random duplicate pair scores higher than a random "same object, other photo" pair. It does not depend on the threshold, so models can be compared fairly. 1.0 means perfect separation, 0.5 means guessing;
- speed was measured on a laptop CPU (Apple Silicon).

## Results

Each model at its own best threshold:

| Model | AUC | Best threshold | Duplicates found | False: same object | False: other object | Images/s |
|---|---|---|---|---|---|---|
| **SSCD** | **0.960** | 0.76 | **89.0%** | **9.6%** | 0.0% | 13 |
| DINOv2 ViT-S/14 | 0.866 | 0.92 | 76.4% | 17.3% | 0.7% | 50 |
| EfficientNet-B0 | 0.849 | 0.88 | 71.8% | 16.0% | 0.0% | 13 |
| ViT-B/16 | 0.832 | 0.87 | 71.2% | 17.1% | 0.0% | 21 |
| ResNet50 | 0.795 | 0.91 | 59.5% | 12.9% | 0.0% | 11 |
| CLIP ViT-B/32 | 0.524 | 0.96 | 23.5% | 17.8% | 1.3% | 77 |

ImageNet classifiers, DINOv2 and especially CLIP are trained to recognize **what** is in a photo. To them, two different shots of the same object look almost identical, so they cannot separate such pairs from real copies. CLIP, with an AUC of 0.52, is close to guessing.

**Each model has its own threshold, and thresholds cannot be compared across models.** For DINOv2, even two different shots of the same object score ~0.93 on average, so it needs a threshold of 0.92. SSCD spreads scores wider (the same pairs average ~0.59), so 0.75 is enough. Within one model, a higher threshold gives fewer false matches but more missed duplicates.

## Conclusion

Two models made it to the final:

- **SSCD is the most accurate.** It finds 89% of duplicates, confuses different photos of the same object half as often, and fully separates different objects.
- **DINOv2 is the fastest of the accurate ones**, about four times faster than SSCD (50 images/s vs 13), but noticeably less accurate: it finds 76% of duplicates with 17% false matches. It uses its own threshold of 0.92.

For this service **accuracy was chosen, so SSCD**. A missed or false duplicate is an error the user sees, while throughput can be increased by adding workers.

## Detailed SSCD results

### Threshold choice

| Threshold | Duplicates found | False: same object | False: other object |
|---|---|---|---|
| 0.60 | 98.7% | 46.2% | 0.0% |
| 0.65 | 97.5% | 34.9% | 0.0% |
| 0.70 | 95.4% | 21.3% | 0.0% |
| **0.75** | **90.2%** | **12.2%** | **0.0%** |
| 0.80 | 79.8% | 6.0% | 0.0% |
| 0.85 | 65.1% | 1.1% | 0.0% |
| 0.90 | 52.0% | 0.0% | 0.0% |

The default is **0.75**. The best balance came out at 0.76, but the difference is within noise, so the round value was taken. Different objects are never confused: the highest similarity between them is 0.37, far below the threshold.

The threshold is set via the `DUPLICATE_THRESHOLD` variable or the `?threshold=` query parameter. If false matches matter more than missed duplicates, it can be raised to 0.80–0.85.

### Similarity by edit type

Median is the typical score for an edit; p5 is the score below which the worst 5% of copies fall.

| Edit | Median | p5 |
|---|---|---|
| brightness −40% | 0.988 | 0.971 |
| downscale 50% | 0.987 | 0.942 |
| contrast −50% | 0.984 | 0.954 |
| contrast +50% | 0.979 | 0.915 |
| brightness +40% | 0.978 | 0.840 |
| JPEG quality 30 | 0.961 | 0.824 |
| horizontal flip | 0.926 | 0.867 |
| 10% crop, centered | 0.912 | 0.826 |
| downscale 25% | 0.911 | 0.791 |
| watermark | 0.888 | 0.789 |
| 20% crop, centered | 0.834 | 0.707 |
| 20% crop, from a corner | 0.818 | 0.736 |
| rotation 5° | 0.815 | 0.740 |
| combination | 0.805 | 0.704 |
| rotation 10° | 0.767 | 0.681 |
| JPEG quality 10 | 0.755 | 0.519 |

Brightness, contrast, size changes and moderate compression are recognized almost always. The weak spots are **10° rotation**, **very heavy compression (JPEG quality 10)** and **20% crop**: their typical score is close to the threshold, so roughly half of such copies will be missed.

### Calibration limitations

- **The sample is small** (150 objects) and of a single kind: objects on a table, 640×480. For real data, the threshold should be checked on your own sample.
- **The edits are synthetic**: generated by a script, not taken from real copies found online.
- **The false-match test is strict.** In UKBench, shots of one object were taken seconds apart on the same background, and some are nearly identical, so 12% false matches is an upper estimate.
