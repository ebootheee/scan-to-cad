# Tile Blender renders into the post's composite figures (originally run inline as python -c).
#   python.exe tile_images.py views     <render_prefix> <out.png>   (prefix from scan/render_views.py)
#   python.exe tile_images.py deviation <render_prefix> <out.png>   (prefix from scan/compare.py)
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.image as im

mode, s, out = sys.argv[1:4]
if mode == "views":
    f, a = plt.subplots(2, 2, figsize=(16, 10.5))
    for x, k, t in zip(a.flat, ['side_neg', 'iso', 'top', 'iso_under'], ['side', 'three-quarter', 'top', 'from below']):
        x.imshow(im.imread(s + '_' + k + '.png')); x.set_title(t, fontsize=16); x.axis('off')
    plt.tight_layout(); plt.savefig(out, dpi=80)
else:
    n = ['side', 'top', 'bottom', 'iso', 'iso_under', 'ends']
    f, a = plt.subplots(2, 3, figsize=(18, 8.6))
    for x, k in zip(a.flat, n):
        x.imshow(im.imread(s + '_' + k + '.png')); x.set_title(k); x.axis('off')
    f.suptitle('Scan coloured by distance from v5   (red = scan outside v5, blue = inside, full colour = 0.4 mm)   rms 0.12 mm, 98% within 0.3 mm')
    plt.tight_layout(); plt.savefig(out, dpi=75)
