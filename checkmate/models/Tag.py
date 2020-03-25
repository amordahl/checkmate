###
# Copyright 2020 by Austin Mordahl
#
# This file is part of checkmate.
#
# checkmate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# checkmate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with checkmate.  If not, see <https://www.gnu.org/licenses/>.
###

from enum import Enum


class Tag(Enum):
    """Tags"""
    OBJECT = 1
    EXCEPTION = 2
    STATIC = 3
    REFLECTION = 4
    TAINT_ANALYSIS_SPECIFIC = 5
    ANDROID_LIFECYCLE = 6
    LIBRARY = 7
