import os
import shutil
from PIL import Image
from jinja2 import Template

# 定义目录
photos_dir = 'photos'  # 原始图片目录
templates_dir = 'templates/times'  # 模板目录
output_dir = 'output'  # 输出目录
thumb_dir = os.path.join(output_dir, 'images/thumbs')  # 缩略图目录
full_dir = os.path.join(output_dir, 'images/fulls')  # 原图目录

# 创建输出目录
os.makedirs(thumb_dir, exist_ok=True)
os.makedirs(full_dir, exist_ok=True)

# 同步模板中的 assets 目录到 output 目录
if os.path.exists(os.path.join(templates_dir, 'assets')):
    shutil.copytree(os.path.join(templates_dir, 'assets'), os.path.join(output_dir, 'assets'), dirs_exist_ok=True)

# 获取图片文件列表（支持子目录）
images = []
for root, dirs, files in os.walk(photos_dir):
    # 查找当前目录下的 `描述.txt` 文件
    description_file = os.path.join(root, '描述.txt')
    default_description = None
    if os.path.exists(description_file):
        with open(description_file, 'r', encoding='utf-8') as f:
            default_description = f.read().strip()  # 读取 `描述.txt` 的内容

    for filename in files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            original_path = os.path.join(root, filename)
            thumb_path = os.path.join(thumb_dir, filename)
            full_path = os.path.join(full_dir, filename)

            try:
                # 打开图片并处理
                with Image.open(original_path) as img:
                    # 如果图片是RGBA模式，转换为RGB模式
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    # 去除 EXIF 信息
                    img.save(full_path, quality=95, exif=b'')

                    # 生成缩略图
                    img.thumbnail((400, 400))  # 缩略图大小 
                    img.save(thumb_path, quality=80)  # 压缩质量

                # 设置标题
                if root == photos_dir:
                    title = '分享生活'  # 根目录下的图片使用默认标题
                else:
                    title = os.path.basename(root)  # 子目录下的图片使用子目录名称作为标题

                # 设置描述
                description = filename  # 默认描述为文件名
                txt_file = os.path.join(root, os.path.splitext(filename)[0] + '.txt')  # 查找同名的txt文件
                if os.path.exists(txt_file):  # 如果存在同名的txt文件
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        description = f.read().strip()  # 读取txt文件内容作为描述
                elif default_description is not None:  # 如果存在 `描述.txt` 文件
                    description = default_description  # 使用 `描述.txt` 的内容作为描述

                # 添加图片信息
                images.append({
                    'full_path': os.path.relpath(full_path, output_dir).replace('\\', '/'),  # 使用相对路径
                    'thumb_path': os.path.relpath(thumb_path, output_dir).replace('\\', '/'),  # 使用相对路径
                    'title': title,  # 使用子目录名称或默认标题
                    'description': description  # 使用txt文件内容或默认描述
                })
            except Exception as e:
                print(f"无法处理文件 {original_path}，错误：{e}")
                continue  # 跳过该文件，继续处理下一个文件

# 分页设置
images_per_page = 12
total_pages = (len(images) + images_per_page - 1) // images_per_page

# 将图片列表分页
paged_images = [images[i:i + images_per_page] for i in range(0, len(images), images_per_page)]

# 读取HTML模板
with open(os.path.join(templates_dir, 'index.html'), 'r', encoding='utf-8') as file:
    template_content = file.read()

# 使用Jinja2模板引擎
template = Template(template_content)

# 生成每页的 HTML 内容
for page_num, page_images in enumerate(paged_images, start=1):
    html_content = template.render(images=page_images, current_page=page_num, total_pages=total_pages)
    if page_num == 1:
        output_file = os.path.join(output_dir, 'index.html')
    else:
        output_file = os.path.join(output_dir, f'index-{page_num}.html')
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"相册第 {page_num} 页已生成，保存为 {output_file}")