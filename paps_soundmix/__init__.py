# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__author__ = "d01"
__email__ = "jungflor@gmail.com"
__copyright__ = "Copyright (C) 2015-16, Florian JUNG"
__license__ = "MIT"
__version__ = "0.2.1"
__date__ = "2016-03-31"
# Created: 2015-07-21 18:23

import logging

from .plugin import SoundMixPlugin
from .leftright import SoundMixLeftRightPlugin
from .angel import Angel

__all__ = ["plugin", "leftright", "angel"]
logger = logging.getLogger(__name__)
