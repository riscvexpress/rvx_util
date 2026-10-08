# ****************************************************************************
# ****************************************************************************
# Copyright SoC Design Research Group, All rights reserved.
# Electronics and Telecommunications Research Institute (ETRI)
# 
# THESE DOCUMENTS CONTAIN CONFIDENTIAL INFORMATION AND KNOWLEDGE
# WHICH IS THE PROPERTY OF ETRI. NO PART OF THIS PUBLICATION IS
# TO BE USED FOR ANY OTHER PURPOSE, AND THESE ARE NOT TO BE
# REPRODUCED, COPIED, DISCLOSED, TRANSMITTED, STORED IN A RETRIEVAL
# SYSTEM OR TRANSLATED INTO ANY OTHER HUMAN OR COMPUTER LANGUAGE,
# IN ANY FORM, BY ANY MEANS, IN WHOLE OR IN PART, WITHOUT THE
# COMPLETE PRIOR WRITTEN PERMISSION OF ETRI.
# ****************************************************************************
# 2019-06-14
# Kyuseung Han (han@etri.re.kr)
# ****************************************************************************
# ****************************************************************************

import argparse
import os
import re
import shlex
from pathlib import Path

from os_util import *
from configure_template import *

LEGACY_VAR_DICT = {'RVX_ENV': 'RVX_DEVKIT_HOME'}

def expand_var(text:str):
	for old_var, new_var in LEGACY_VAR_DICT.items():
		text = text.replace(f'${{{old_var}}}', f'${{{new_var}}}')
	return os.path.expandvars(text)

def get_makefile_var(contents:str, name:str):
	match = re.search(rf'^{name}\s*=\s*(.*)$', contents, re.MULTILINE)
	return match.group(1).strip() if match else None

def update_makefile(makefile:Path):
	contents = makefile.read_text(encoding='utf8')
	template = get_makefile_var(contents, 'TEMPLATE_FILE')
	if not template:
		return
	template_file = Path(expand_var(template))
	assert template_file.is_file(), (template_file, makefile)
	print(makefile)
	template_config = get_makefile_var(contents, 'TEMPLATE_CONFIG')
	if template_config:
		conv_dict = dict(x.split('=', 1) for x in shlex.split(template_config))
		configure_template_file(template_file, makefile, conv_dict)
	else:
		copy_file(template_file, makefile)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Update Makefile')
	parser.add_argument('-path', '-p', help='path')
	args = parser.parse_args()

	assert args.path
	base_path = Path(args.path).resolve()

	for makefile in base_path.glob('**/Makefile'):
		if 'template_makefile.mh' in makefile.read_text(encoding='utf8'):
			update_makefile(makefile)
