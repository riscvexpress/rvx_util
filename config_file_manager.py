import os
import argparse
import getpass
from pathlib import Path
import xml.etree.ElementTree as XmlTree
from xml.dom import minidom

from os_util import *
from xml_util import *
from misc_util import *

class ConfigFileManager():
  def __init__(self, cfg_name:str, file_path:Path):
    self.name = None
    self.file_path = None
    self.attr_dict = {}
    self.equal_to_file = False

    assert cfg_name
    self.name = cfg_name
    assert file_path
    self.file_path = file_path
    self.import_file()

  def __repr__(self):
    result  = f'<{self.name}>'
    for name, value in self.attr_dict.items():
      result += f'\n{name}={value}'
    return result

  def set_attr(self, name:str, value):
    self.attr_dict[name] = value
    self.equal_to_file = False

  def set_attr_from_input(self, name:str, question:str=None, allowed_value_type_or_list=None, hides_input:bool=False):
    prompt = ''
    if question:
      prompt += question
    else:
      prompt += f'{name.capitalize()}?'
    allowed_value_list = []
    if allowed_value_type_or_list:
      value_type = type(allowed_value_type_or_list)
      prompt += ' '
      if allowed_value_type_or_list=='int':
        prompt += '(int)'
      elif allowed_value_type_or_list=='bool':
        prompt += '(bool)'
      elif value_type==list or value_type==tuple:
        for allowed_value in allowed_value_type_or_list:
          allowed_value_list.append(str(allowed_value))
        prompt += '({0})'.format(','.join([ f'[{i}]{x}' for i, x in enumerate(allowed_value_list) ]))
    prompt += ' : '

    while 1:
      if hides_input:
        answer = getpass.getpass(prompt)
      else:
        answer = input(prompt)

      if allowed_value_type_or_list=='int':
        try:
          answer = int(answer)
          break
        except:
          print('Not integer.')
          pass
      elif allowed_value_type_or_list=='bool':
        answer = answer2bool(answer)
        break
      elif not allowed_value_list:
        break
      else:
        if answer in allowed_value_list:
          break
        try:
          answer = int(answer)
          if answer < len(allowed_value_list):
            answer = allowed_value_list[answer]
            break
        except:
          pass
      print('Inappropriate answer. Type again.')
    self.set_attr(name, answer)
    return answer

  def keys(self):
    return self.attr_dict.keys()
  
  def __getattr__(self, name:str):
    if name in self.__dict__.keys():
      result = self.__dict__[name]
    elif name in self.attr_dict.keys():
      result = self.attr_dict[name]
    else:
      assert 0, name
    return result
  
  def get_attr(self, name:str):
    return self.attr_dict.get(name)

  def clear(self):
    self.attr_dict = {}
    self.equal_to_file = False
    if self.file_path.is_file():
      remove_file(self.file_path)

  def __iter__():
    return self.attr_dict.items()

  def import_file(self, path:Path=None):
    input_path = path if path else self.file_path
    assert input_path
    success = True
    while 1:
      if not input_path.is_file():
        success = False
        break
      xml_root = read_xml_file(input_path)
      if xml_root.tag!=self.name:
        success = False
        break
      for config in xml_root:
        variable_name = config.tag
        # encrypted values written by old versions can NOT be read
        if config.attrib.get('encoded')=='True':
          success = False
          break
        variable_value = config.text
        if variable_value is None or variable_value=='None':
          variable_value = None
        elif variable_name.endswith('_path'):
          variable_value = Path(variable_value)
        elif variable_value=='True':
          variable_value = True
        elif variable_value=='False':
          variable_value = False
        self.set_attr(variable_name, variable_value)
      break
    if success:
      self.equal_to_file = True
    else:
      self.clear()
    return success
  
  def __export_as_xml(self):
    xml_root = XmlTree.Element(self.name)
    for name, value in self.attr_dict.items():
      xml_element = XmlTree.SubElement(xml_root, name)
      if value is not None:
        xml_element.text = str(value)
    return xml_root

  def export_file(self, path:Path=None):
    output_path = path if path else self.file_path
    assert output_path
    if (not self.equal_to_file) or (output_path!=self.file_path):
      remove_file(output_path)
      xml_root = self.__export_as_xml()
      xml_str = convert_xml_to_text(xml_root)
      with open(output_path, 'w', encoding='utf8', newline='\n') as f:
        f.write(xml_str)
      self.equal_to_file = True

  def check(self, allowed_set, matches_exactly=False):
    result = True
    while 1:
      if matches_exactly and (len(self.attr_dict)!=len(allowed_set)):
        result = False
        break
      for key in self.attr_dict.keys():
        if key not in allowed_set:
          result = False
          break
      break
    return result

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='ConfigFileManager Manager')
  parser.add_argument('-name', help='configuration name')
  parser.add_argument('-file', '-f', help='configuration file')
  parser.add_argument('-cmd', '-c', help='command')
  parser.add_argument('-cfg', nargs='+', help='attribute list')
  parser.add_argument('-result', '-o', help='result file')
  args = parser.parse_args()

  assert args.cmd
  assert args.name
  assert args.file
  config = ConfigFileManager(args.name, Path(args.file).resolve())
  if args.cmd=='set':
    if args.cfg:
      attribute_list = []
      for concated_attr in args.cfg:
        name, value = concated_attr.split(':')
        attribute_list.append((name,value))
      for name, value in attribute_list:
        config.set_attr(name, value)
      config.export_file()
  elif args.cmd=='get':
    attribute_list = args.cfg
    if not attribute_list:
      attribute_list = []
    result_list = []
    for name in attribute_list:
      result_list.append(f'{name}:{config.get_attr(name)}')
    result = '\n'.join(result_list)
    if args.result:
      Path(args.result).write_text(result, encoding='utf8')
    else:
      print(result)
  elif args.cmd=='print':
    if args.result:
      Path(args.result).write_text(config, encoding='utf8')
    else:
      print(config)
  else:
    assert 0, args.cmd
