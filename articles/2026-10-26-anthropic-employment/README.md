# Anthropic内部就业报告配套资料

版本：v1.0.0；更新时间：2026-10-26。

本资料提供初级技术人员占比对照图、AI协作任务检查流程、绘图源码、封面PNG及可编辑SVG模板。

数据来自Anthropic于2026年10月16日发布的《How employment is changing at Anthropic》：
https://www.anthropic.com/research/employment-at-anthropic

图1采用报告正文公布的取整端点，分别以技术新招聘人数、技术在职人数为分母。图2是作者整理的实践流程。

## 使用方法

安装Python 3.10或更新版本，执行：

```powershell
python -m pip install -r requirements.txt
python 绘图.py
```

绘图脚本优先使用系统中文字体，生成正文两张图、横版与方版可编辑SVG模板及对应PNG。可在矢量编辑器中单独修改SVG里的文字、形状和配色。AI概念封面采用内置imagegen生成，提示词见《封面提示词.txt》。

## 文件说明

- `数据/数据与来源.json`：原报告入口、数据端点、分母、核对位置和解释范围。
- `绘图.py`：图表、流程图与封面模板的可复现源码。
- `配图/`：正文图、概念封面、SVG模板及PNG。
- `物料清单.json`：文件大小与SHA-256校验值。

绘图署名：可以叫我才哥。封面为概念插画。
