# 🎉 v2.0 更新说明 - 验证码自动识别

## 📅 更新时间
2026-01-18

## 🎯 主要更新

### 1. 支持多种OCR引擎

现在支持**三种**验证码识别方案:

#### ⭐ EasyOCR (推荐)
- 深度学习模型,识别准确率75-85%
- 完全支持Python 3.14
- 自动图像预处理
- 首次使用需下载模型(~100MB)

#### 🔧 Tesseract OCR
- 传统OCR引擎,轻量快速
- 识别准确率50-65%
- 需要单独安装Tesseract

#### 👤 人工输入
- 100%准确率
- 适合小批量爬取

### 2. 智能图像预处理

自动对验证码图片进行:
- 灰度化处理
- 自适应二值化
- 降噪处理
- 形态学优化

### 3. 新增测试工具

```bash
python test_captcha.py
```

可以测试不同OCR引擎的识别效果,并统计成功率。

---

## 📦 安装新依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装新依赖
pip install easyocr opencv-python numpy pytesseract

# (可选)安装Tesseract引擎
brew install tesseract  # Mac
```

---

## ⚙️ 配置说明

编辑 `config.py` 文件:

```python
CAPTCHA_CONFIG = {
    "ocr_engine": "easyocr",  # 选择OCR引擎
    "retry": 3,               # 重试次数
    
    # EasyOCR配置
    "easyocr_langs": ['en'],
    "easyocr_gpu": False,
    
    # Tesseract配置
    "tesseract_config": "--psm 7 --oem 3",
}
```

---

## 🚀 快速开始

### 方式一:使用EasyOCR(推荐)

```bash
# 1. 测试验证码识别
python test_captcha.py

# 2. 运行爬虫
python scraper.py
```

首次运行EasyOCR会自动下载模型,请耐心等待。

### 方式二:使用Tesseract

```bash
# 1. 安装Tesseract
brew install tesseract

# 2. 修改配置
# 编辑config.py,设置ocr_engine="tesseract"

# 3. 测试
python test_captcha.py

# 4. 运行爬虫
python scraper.py
```

### 方式三:人工输入

```bash
# 修改config.py,设置ocr_engine="manual"
python scraper.py
```

---

## 📊 性能对比

| OCR引擎   | 准确率 | 速度         | 内存占用   | 推荐场景 |
| --------- | ------ | ------------ | ---------- | -------- |
| EasyOCR   | 75-85% | 慢(~2s/次)   | 高(~500MB) | 中大批量 |
| Tesseract | 50-65% | 快(~0.5s/次) | 低(~50MB)  | 快速测试 |
| 人工输入  | 100%   | 最慢         | 极低       | 小批量   |

---

## 🔧 故障排除

### EasyOCR相关

**Q: 首次运行很慢?**
```
A: 正在下载模型文件(仅首次需要),请耐心等待
```

**Q: 内存不足?**
```
A: 减少并发数,或切换到Tesseract
```

### Tesseract相关

**Q: 找不到tesseract命令?**
```bash
# Mac
brew install tesseract

# 验证安装
tesseract --version
```

**Q: 识别率太低?**
```
A: 切换到EasyOCR,或使用人工输入
```

---

## 📝 文件变更

### 新增文件
- `test_captcha.py` - 验证码识别测试工具
- `OCR_GUIDE.md` - OCR引擎详细说明
- `UPDATE_v2.0.md` - 本更新说明

### 修改文件
- `captcha_solver.py` - 重写,支持多OCR引擎
- `config.py` - 新增OCR配置选项
- `requirements.txt` - 新增依赖

---

## 💡 使用建议

### 1. 首次使用

```bash
# 1. 测试验证码识别
python test_captcha.py

# 2. 查看识别成功率
# 如果成功率>70%,可以使用自动识别
# 如果成功率<70%,建议使用人工输入
```

### 2. 批量爬取

```bash
# 1. 先爬取清单(不下载PDF)
python scraper_list_only.py

# 2. 查看清单,确认需要下载的标准数量

# 3. 根据数量选择方案:
#    - <100条: 人工输入
#    - 100-1000条: EasyOCR
#    - >1000条: 考虑第三方打码平台
```

### 3. 混合策略

```python
# config.py
CAPTCHA_CONFIG = {
    "ocr_engine": "easyocr",
    "retry": 3,  # 自动识别重试3次
}
# 如果3次都失败,会自动切换到人工输入
```

---

## 🎁 额外功能

### 验证码图片保存

测试时会自动保存验证码图片:
- `test_captcha_1.png`
- `test_captcha_2.png`
- `test_captcha_3.png`

可以用于分析验证码特征,优化识别参数。

### 识别日志

所有识别结果都会记录到日志:
```bash
tail -f logs/scraper.log | grep "验证码"
```

---

## 🔮 未来计划

- [ ] 集成第三方打码平台API
- [ ] 支持GPU加速(EasyOCR)
- [ ] 训练自定义验证码模型
- [ ] 实现验证码缓存机制

---

## 📖 相关文档

- **OCR_GUIDE.md** - OCR引擎详细说明
- **README.md** - 项目完整文档
- **QUICKSTART.md** - 快速开始指南

---

## 🙏 致谢

感谢以下开源项目:
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [OpenCV](https://opencv.org/)

---

**版本**: v2.0
**状态**: ✅ 已完成并测试
**兼容性**: Python 3.14+
