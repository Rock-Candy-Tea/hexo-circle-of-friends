# -*- coding:utf-8 -*-
# Author：yyyz
import yaml

with open("../fc_settings.yaml", 'r', encoding="utf-8") as f:
    a = yaml.safe_load(f)
    a["123"] = 456
    print(a)

with open("../dump_settings", 'w', encoding="utf-8") as f:
    yaml.safe_dump(a,f)


with open("../dump_settings", 'r', encoding="utf-8") as f:
    a = yaml.safe_load(f)
    print(a)
