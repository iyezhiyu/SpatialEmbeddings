"""
Author: Davy Neven
Licensed under the CC BY-NC 4.0 license (https://creativecommons.org/licenses/by-nc/4.0/)
"""
import math

import numpy as np

import torch
import torch.nn as nn
from criterions.lovasz_losses import lovasz_hinge


class SpatialEmbLoss(nn.Module):

    def __init__(self, to_center=True, n_sigma=1, foreground_weight=[1,1,1,1,1,1,1,1,1],):
        super().__init__()

        
        print('Created spatial emb loss function with: to_center: {}, n_sigma: {}, foreground_weight: {}'.format(
            to_center, n_sigma, foreground_weight))

        self.to_center = to_center
        self.n_sigma = n_sigma
        self.foreground_weight = foreground_weight

        # coordinate map
        xm = torch.linspace(0, 2, 2048).view(
            1, 1, -1).expand(1, 1024, 2048)
        ym = torch.linspace(0, 1, 1024).view(
            1, -1, 1).expand(1, 1024, 2048)
        xym = torch.cat((xm, ym), 0)

        self.register_buffer("xym", xym)

    def forward(self, prediction, instances, labels, w_inst=1, w_var=1, w_seed=1, iou=False, iou_meter=None):

        batch_size, height, width = prediction.size(
            0), prediction.size(2), prediction.size(3)

        xym_s = self.xym[:, 0:height, 0:width].contiguous()  # 2 x h x w

        loss = 0

        for b in range(0, batch_size):

            spatial_emb = torch.tanh(prediction[b, 0:2]) + xym_s  # 2 x h x w
            sigma = prediction[b, 2:2+self.n_sigma]  # n_sigma x h x w
            seed_map = torch.sigmoid(
                prediction[b, 2+self.n_sigma:2+self.n_sigma + 8])  # 8 x h x w, 8个class

            # loss accumulators
            var_loss = 0
            instance_loss = 0
            seed_loss = 0
            obj_count = 0

            instance = instances[b].unsqueeze(0)  # 1 x h x w
            label = labels[b].unsqueeze(0)  # 1 x h x w

            instance_ids = instance.unique()
            instance_ids = instance_ids[instance_ids != 0]

            # regress bg to zero
            for i in range(1, 9):
                bg_mask = (label != i)
                if bg_mask.sum() > 0:
                    #print("=============")
                    #print(i)
                    #print(bg_mask.shape)
                    #print(seed_map.shape)
                    #print(seed_map[i-1].unsqueeze(0).shape)
                    seed_loss += torch.sum(torch.pow((seed_map[i-1].unsqueeze(0))[bg_mask] - 0, 2))

            for id in instance_ids:

                in_mask = instance.eq(id)   # 1 x h x w

                class_id = int(np.unique(label[in_mask].cpu().numpy()))

                # calculate center of attraction
                if self.to_center:
                    xy_in = xym_s[in_mask.expand_as(xym_s)].view(2, -1)
                    center = xy_in.mean(1).view(2, 1, 1)  # 2 x 1 x 1
                else:
                    center = spatial_emb[in_mask.expand_as(spatial_emb)].view(
                        2, -1).mean(1).view(2, 1, 1)  # 2 x 1 x 1

                # calculate sigma
                sigma_in = sigma[in_mask.expand_as(
                    sigma)].view(self.n_sigma, -1)

                s = sigma_in.mean(1).view(
                    self.n_sigma, 1, 1)   # n_sigma x 1 x 1

                # calculate var loss before exp
                var_loss = var_loss + \
                    torch.mean(
                        torch.pow(sigma_in - s.detach(), 2))

                s = torch.exp(s*10)

                # calculate gaussian
                dist = torch.exp(-1*torch.sum(
                    torch.pow(spatial_emb - center, 2)*s, 0, keepdim=True))

                # apply lovasz-hinge loss
                instance_loss = instance_loss + \
                    lovasz_hinge(dist*2-1, in_mask)

                # seed loss
                seed_loss += self.foreground_weight[class_id-1] * torch.sum(
                    torch.pow(seed_map[class_id-1][in_mask.squeeze(0)].unsqueeze(0) - dist[in_mask].detach(), 2))

                # calculate instance iou
                if iou:
                    iou_meter.update(calculate_iou(dist > 0.5, in_mask))

                obj_count += 1

            if obj_count > 0:
                instance_loss /= obj_count
                var_loss /= obj_count

            seed_loss = seed_loss / (height * width)

            loss += w_inst * instance_loss + w_var * var_loss + w_seed * seed_loss

        loss = loss / (b+1)

        return loss + prediction.sum()*0


def calculate_iou(pred, label):
    intersection = ((label == 1) & (pred == 1)).sum()
    union = ((label == 1) | (pred == 1)).sum()
    if not union:
        return 0
    else:
        iou = intersection.item() / union.item()
        return iou
