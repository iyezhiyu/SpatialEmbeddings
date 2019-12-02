# Instance segmentation by jointly optimizing spatial embeddings and clustering bandwidth (elliptical)

This codebase implements the loss function described in: 

[Instance Segmentation by Jointly Optimizing Spatial Embeddings and Clustering Bandwidth](https://arxiv.org/pdf/1906.11109.pdf)
Davy Neven, Bert De Brabandere, Marc Proesmans, and Luc Van Gool
Conference on Computer Vision and Pattern Recognition (CVPR), june 2019

Our network architecture is a multi-branched version of [ERFNet](https://github.com/Eromera/erfnet_pytorch) and uses the [Lovasz-hinge loss](https://github.com/bermanmaxim/LovaszSoftmax) for maximizing the IoU of each instance.

<p align="center">
    <img src="static/teaser.jpg" />
</p>

## TODO

Modified the code to the elliptical version

## License

This software is released under a creative commons license which allows for personal and research use only. For a commercial license please contact the authors. You can view a license summary [here](http://creativecommons.org/licenses/by-nc/4.0/).

## Getting started

This codebase showcases the proposed loss function with the elliptical margin version on car instance segmentation using the Cityscapes dataset. 

### Prerequisites
Dependencies: 
- Pytorch 1.1
- Python 3.6.8  (or higher)
- [Cityscapes](https://www.cityscapes-dataset.com/) + [scripts](https://github.com/mcordts/cityscapesScripts) (if you want to evaluate the model)

## Training
Training consists out of 2 steps. We first train on 512x512 crops around each object, to avoid computation on background patches. Afterwards, we finetune on larger patches (1024x1024) to account for bigger objects and background features which are not present in the smaller crops. 

To generate these crops do the following:
```
$ sh generate.sh
``` 

Afterwards start training: 
```
$ sh train.sh
```

Different options can be modified in `train_config.py`, e.g. to visualize set `display=True`.

## Testing

Save the pretrained models in the src/pretrained_models/ or adapt the test_config.py file.

To test the model on the Cityscapes validation set run:

```
$ sh test.sh
```

## Acknowledgement
This work was supported by Toyota, and was carried out at the TRACE Lab at KU Leuven (Toyota Research on Automated Cars in Europe - Leuven)








