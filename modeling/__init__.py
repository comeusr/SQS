from __future__ import print_function

import torch.nn as nn
from composer.models import ComposerModel

from .networks import get_network
from modeling.DGMS import DGMSConv
import torch.nn.functional as F

class DGMSNet(ComposerModel):
    def __init__(self, args, freeze_bn=False):
        super(DGMSNet, self).__init__()
        self.args = args
        self.network = get_network(args)
        self.freeze_bn = freeze_bn

    def init_mask_params(self):
        print("--> Start to initialize sub-distribution parameters, this may take some time...")
        for name, m in self.network.named_modules():
            if isinstance(m, DGMSConv):
                m.init_mask_params()
            m.init

        print("--> Sub-distribution parameters initialization finished!")

    def forward(self, batch):
        inputs, _ = batch
        return self.network(inputs)

    def get_1x_lr_params(self):
        self.init_mask_params()
        modules = [self.network]
        for i in range(len(modules)):
            for m in modules[i].named_modules():
                if self.freeze_bn:
                    if isinstance(m[1], nn.Conv2d):
                        if self.args.freeze_weights:
                            for p in m[1].parameters():
                                pass
                        else:
                            for p in m[1].parameters():
                                if p.requires_grad:
                                    yield p
                else:
                    for p in m[1].parameters():
                        if p.requires_grad:
                            yield p

    def loss(self, outputs, batch):
        _, targets = batch
        return F.cross_entropy(outputs, targets)


class DGMSComposerNet(ComposerModel):

    def __init__(self, args):
        super(DGMSComposerNet, self).__init__()
        self.network = DGMSNet(args, args.freeze_bn)

    def forward(self, batch):
        inputs, _ = batch
        return self.network(inputs)

    def loss(self, outputs, batch):
        _, targets=batch
        return F.cross_entropy(outputs, targets)

