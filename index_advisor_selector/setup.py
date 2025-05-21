from setuptools import setup, find_packages
import os

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

setup(
    name="index_advisor_selector",  # 项目名称（自定义）
    version="0.1.0",               # 版本号
    author="Your Name",            # 作者
    description="Index Advisor Selector Tool",  # 简短描述

    # 关键配置：定义包的位置和包含的模块
    packages=find_packages(where="."),  # 自动发现所有包
    # 或手动指定包名（如果自动发现失败）:
    # packages=["index_selection.swirl_selection"],

    # 指定包所在根目录（重要！）
    package_dir={
        "": ".",  # 表示从当前目录查找包
    },

    # 依赖项（根据需求添加）
    install_requires=[

    ],
)