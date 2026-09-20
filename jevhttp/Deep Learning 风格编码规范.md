# Deep Learning 风格编码规范

## 引言

本文档为深度学习项目的 Python 代码提供编码规范，涵盖代码布局、命名约定、注释风格、模型定义模式、训练循环组织、数据处理流程等方面。

规范的目的是帮助深度学习工程师和研究者保持代码一致性，减少沟通成本，使代码更容易阅读、复用和维护。本规范会随着社区实践的发展而演进。当项目自身的风格与本规范冲突时，项目风格优先。

---

## 代码布局

### 缩进

每个缩进级别使用 4 个空格。

```python
# Correct:
def forward(self, X):
    Y = self.conv1(X)
    return F.relu(Y)
```

续行与起始定界符对齐，或使用悬挂缩进（额外 4 个空格）。

```python
# Correct — 与起始定界符对齐：
net = nn.Sequential(nn.Linear(784, 256),
                    nn.ReLU(),
                    nn.Linear(256, 10))

# Correct — 悬挂缩进（额外 4 空格）：
net = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Linear(256, 10),
)
```

### 最大行宽

每行不超过 **100 字符**。深度学习代码常涉及较长的张量形状注释和模块堆叠表达式，100 字符在可读性和屏幕适配之间取得平衡。

对于过长的函数签名、字符串或条件表达式，使用括号进行隐式续行：

```python
# Correct:
output = self.linear(Y.reshape((-1, Y.shape[-1])))

# Correct:
return (data.DataLoader(mnist_train, batch_size, shuffle=True,
                        num_workers=get_dataloader_workers()),
        data.DataLoader(mnist_test, batch_size, shuffle=False,
                        num_workers=get_dataloader_workers()))
```

### 二元操作符换行

操作符放在新行的开头：

```python
# Correct:
loss = (y_hat - y.reshape(y_hat.shape)) ** 2 / 2

# Correct:
output = (self.pos_encoding(self.embedding(X)
          * math.sqrt(self.num_hiddens)))
```

### 空行

- 模块级函数和类定义之间：两行空行
- 类中方法定义之间：一行空行
- 代码块之间不要随意插入空行，空行意味着逻辑段落的分隔

### 导入

导入按以下顺序分组，每组之间空一行，组内按字母序排列：

```python
# 1. 标准库
import argparse
import logging
import math
import os
import random
import sys
from pathlib import Path

# 2. 第三方库
import numpy as np
import torch
import torch.nn.functional as F
from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
from matplotlib import pyplot as plt
from torch import nn
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

# 3. transformers 生态
from transformers import (
    AutoConfig,
    AutoModel,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

# 4. PEFT
from peft import (
    LoraConfig,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
```

导入原则：

- 优先从模块导入具体的类或函数，而非整个模块
- `torch.nn.functional` 统一导入为 `F`
- `transformers` 的 Auto 类集中放在一起
- 禁止使用通配符导入（`from module import *`）

```python
# Correct:
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained(model_name)

# Wrong:
import transformers
model = transformers.AutoModel.from_pretrained(model_name)
```

---

## 字符串引号

代码中使用**单引号** `'...'`，文档字符串使用三重双引号 `"""..."""`。

```python
# Correct:
text_labels = ['t-shirt', 'trouser', 'pullover', 'dress']
print(f'loss {train_l:.3f}, train acc {train_acc:.3f}')

def accuracy(y_hat, y):
    """计算预测正确的数量"""
    ...
```

---

## 表达式和语句中的空白

### 二元操作符

二元操作符两侧各加一个空格：

```python
# Correct:
num_inputs, num_outputs, num_hiddens = 784, 10, 256
loss = (y_hat - y) ** 2 / 2
```

### 函数参数

函数参数列表中逗号后加一个空格，默认参数值 `=` 两侧不加空格：

```python
# Correct:
def train_ch6(net, train_iter, test_iter, num_epochs, lr, device):
    ...

# Correct:
def __init__(self, key_size, query_size, value_size, num_hiddens,
             num_heads, dropout, bias=False, **kwargs):
    ...
```

### 注释中的空白

注释 `#` 后跟一个英文半角空格。若注释与代码同行，`#` 前留两个英文半角空格：

```python
# Correct:
net.eval()  # 将模型设置为评估模式

# Correct:
# 训练损失总和、训练准确度总和、样本数
metric = Accumulator(3)
```

注释中中文与英文/数字之间不加空格：

```python
# Correct:
# 迭代周期数num_epochs和批量大小batch_size
# 输出形状:(batch_size,查询的个数,num_hiddens)

# Wrong:
# 迭代周期数 num_epochs 和批量大小 batch_size
```

### 禁止的空白

- 紧贴括号内侧：`spam(ham[1], {eggs: 2})`，不是 `spam( ham[ 1 ], { eggs: 2 } )`
- 紧贴逗号/分号/冒号前：`if x == 4:`，不是 `if x == 4 :`
- 切片中 `:` 两侧各加一个空格，但如果一侧为省略值则不留空格：`X[:, :, 0::2]`

---

## 注释

### 注释语言

注释使用**中文**，句末不加句号。符号引用使用英文标点：

```python
# Correct:
# 这里X的形状：(批量大小, 词数)
# 因为位置编码值在-1和1之间，因此嵌入值需要缩放

# 形状中使用英文标点：
# output的形状:(batch_size*num_heads,num_hiddens/num_heads)
```

### 块注释

块注释解释"为什么这样做"而非"代码做了什么"：

```python
# Correct:
# 在第一次迭代或使用随机抽样时初始化state
if state is None or use_random_iter:
    state = net.begin_state(batch_size=X.shape[0], device=device)

# Wrong:
# 如果state是None或use_random_iter为True
if state is None or use_random_iter:
    state = net.begin_state(batch_size=X.shape[0], device=device)
```

### 行内注释

行内注释应与其引用的代码在同一行，且与代码之间至少有两个空格。行内注释应简洁，只用于非显而易见的逻辑：

```python
# Correct:
X = X.reshape(-1, num_heads, X.shape[1], X.shape[2])  # 多注意力头并行计算
X = X.permute(0, 2, 1, 3)                             # 交换维度以适配批量矩阵乘法
```

### 文档字符串

每个公开函数和类必须有文档字符串。格式：

```python
def synthetic_data(w, b, num_examples):
    """生成y=Xw+b+噪声"""
    X = torch.normal(0, 1, (num_examples, len(w)))
    y = torch.matmul(X, w) + b
    y += torch.normal(0, 0.01, y.shape)
    return X, y.reshape((-1, 1))
```

- 单行简短函数：一行摘要即可
- 复杂函数/类：摘要行 + 参数说明 + 返回值说明
- 摘要行使用中文，动词开头
- 保留 `` 符号标记代码中的变量名、函数名等内容

---

## 命名约定

### 首要原则

读者优先。变量名应使深度学习从业者无需查阅文档即可理解其含义。

### 命名风格

| 类型 | 风格 | 示例 |
|------|------|------|
| 变量名 | `snake_case` | `num_epochs`, `batch_size`, `learning_rate` |
| 简短循环变量 | 单字母或简短小写 | `X`, `y`, `y_hat`, `i`, `j`, `w`, `b` |
| 函数名 | `snake_case` | `train_ch6`, `evaluate_accuracy`, `load_data_fashion_mnist` |
| 类名 | `CapWords` | `Accumulator`, `Animator`, `MultiHeadAttention` |
| 方法名 | `snake_case` | `begin_state`, `init_weights`, `to_tokens` |
| 模块名 | `snake_case` | `torch_utils`, `data_pipeline` |
| 常量 | `UPPER_CASE` | `DATA_URL`, `DATA_HUB` |

### 深度学习专用命名约定

以下变量名在深度学习代码中统一使用，不得混用：

#### 模型与训练配置

| 变量名 | 含义 | 说明 |
|--------|------|------|
| `model` | 模型实例 | 使用 transformers 时优先用 `model` |
| `net` | 模型实例 | 纯 PyTorch 手写模型时使用 |
| `tokenizer` | 分词器 | AutoTokenizer 实例 |
| `model_name` | 预训练模型标识 | 如 `'bert-base-uncased'` |
| `loss` | 损失函数 | 不使用 `criterion` |
| `lr` | 学习率 | 不使用 `learning_rate` |
| `num_epochs` | 迭代周期数 | epoch 计数从 1 开始 |
| `batch_size` | 批量大小 | |
| `num_hiddens` | 隐藏单元数 | 不使用 `hidden_size` 或 `n_hidden` |
| `num_inputs` | 输入特征维度 | |
| `num_outputs` | 输出类别数/标签数 | |
| `num_layers` | 网络层数 | |
| `num_heads` | 注意力头数 | |
| `num_steps` | 时间步数/最大序列长度 | |
| `num_labels` | 分类标签数 | transformers 中常用 |
| `device` | 计算设备 | `torch.device('cuda:0')` |

#### 数据

| 变量名 | 含义 |
|--------|------|
| `dataset` | 单个 Dataset 对象 |
| `datasets` | DatasetDict，含 train/validation/test 等划分 |
| `tokenized_dataset` | 经分词处理后的 Dataset 或 DatasetDict |
| `X`, `y` | 小批量特征和标签 |
| `y_hat` | 模型预测值（logits） |
| `features` | 数据集特征张量 |
| `labels` | 数据集标签张量 |
| `train_dataset` | 训练集（Dataset 对象） |
| `eval_dataset` | 验证/评估集（Dataset 对象） |
| `data_collator` | 数据整理器，如 DataCollatorWithPadding |

#### 参数

| 变量名 | 含义 |
|--------|------|
| `w`, `W` | 权重 |
| `b` | 偏置 |
| `params` | 参数列表 |

#### 状态

| 变量名 | 含义 |
|--------|------|
| `state` | RNN 隐藏状态 |
| `enc_outputs` | 编码器输出 |
| `dec_state` | 解码器状态 |
| `valid_len` | 有效长度（序列数据） |
| `input_ids` | 分词后的 token ID 张量 |
| `attention_mask` | 注意力掩码 |

#### 指标

| 变量名 | 含义 |
|--------|------|
| `acc` | 准确率 |
| `train_acc` | 训练准确率 |
| `eval_acc` | 评估准确率 |
| `train_loss` | 训练损失 |
| `eval_loss` | 评估损失 |

### 应避免的命名

- 不使用单字母变量名（除非是循环索引或数学推导中含义明确的符号）
- 不使用 `n_` 前缀（如 `n_epochs`），统一用 `num_` 前缀
- 不使用随机缩写：`num_epochs` 而非 `nepoch` 或 `n_epoch`
- 不使用 `l`（小写 L）作为变量名，易与数字 1 混淆。用 `loss` 或 `train_l`

### 函数命名模式

训练相关函数遵循统一后缀：

| 模式 | 示例 |
|------|------|
| `train_ch*` | `train_ch3`, `train_ch6`, `train_ch8` |
| `train_epoch_ch*` | `train_epoch_ch3`, `train_epoch_ch8` |
| `predict_*` | `predict_ch3`, `predict_ch8`, `predict_seq2seq` |
| `evaluate_*` | `evaluate_accuracy`, `evaluate_loss`, `evaluate_accuracy_gpu` |
| `load_data_*` | `load_data_fashion_mnist`, `load_data_time_machine` |
| `load_array` | 构造 PyTorch 数据迭代器 |

---

## 模型定义

### 优先使用预训练模型

有现成预训练模型时直接加载，不要重新造轮子。核心依赖为 `torch` + `transformers` + `datasets` + `peft` + `bitsandbytes` + `accelerate`。

### 加载预训练模型

使用 Auto 类加载模型和分词器，指定 `num_labels` 适配下游任务：

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_name = 'bert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=2,
    id2label={0: 'NEGATIVE', 1: 'POSITIVE'},
    label2id={'NEGATIVE': 0, 'POSITIVE': 1},
)
```

对于生成式模型（如 Llama、Qwen），使用对应的 Auto 类：

```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,       # 节省显存
    device_map='auto',                # 自动多卡分配
    trust_remote_code=True,           # 自定义模型需要
)
```

### 保存与加载

始终同时保存模型和分词器：

```python
# Correct — 同时保存模型和分词器
model.save_pretrained('./saved_model')
tokenizer.save_pretrained('./saved_model')

# 加载时
model = AutoModelForSequenceClassification.from_pretrained('./saved_model')
tokenizer = AutoTokenizer.from_pretrained('./saved_model')
```

仅保存 LoRA/PEFT 适配器时使用 `merge_and_unload` 或单独保存 adapter 权重。

### nn.Module 子类化规范

当需要自定义架构时，遵循标准的 `nn.Module` 子类化：

```python
class Residual(nn.Module):
    """残差块"""
    def __init__(self, input_channels, num_channels,
                 use_1x1conv=False, strides=1):
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, num_channels,
                               kernel_size=3, padding=1, stride=strides)
        self.conv2 = nn.Conv2d(num_channels, num_channels,
                               kernel_size=3, padding=1)
        if use_1x1conv:
            self.conv3 = nn.Conv2d(input_channels, num_channels,
                                   kernel_size=1, stride=strides)
        else:
            self.conv3 = None
        self.bn1 = nn.BatchNorm2d(num_channels)
        self.bn2 = nn.BatchNorm2d(num_channels)

    def forward(self, X):
        Y = F.relu(self.bn1(self.conv1(X)))
        Y = self.bn2(self.conv2(Y))
        if self.conv3:
            X = self.conv3(X)
        Y += X
        return F.relu(Y)
```

要点：
- `__init__` 中注册所有子层（即使某些条件下不使用，也初始化为 `None`）
- `forward` 方法接收 `X`，返回输出张量
- 残差连接写法：`Y += X` 后接激活函数
- 可选子层用 `if self.conv3` 控制分支

---

## 训练

### 推荐方式：使用 Trainer

优先使用 `transformers.Trainer`，它已集成分布式训练、混合精度、日志记录、checkpoint 管理等：

```python
from transformers import Trainer, TrainingArguments, DataCollatorWithPadding
import numpy as np

def compute_metrics(eval_pred):
    """使用纯 numpy 计算指标，不依赖 sklearn"""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    correct = (predictions == labels).sum()
    total = labels.shape[0]
    return {
        'accuracy': correct / total,
    }

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    learning_rate=2e-5,
    weight_decay=0.01,
    warmup_ratio=0.06,

    # 评估与保存策略
    eval_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    metric_for_best_model='eval_loss',
    save_total_limit=2,

    # 性能
    fp16=torch.cuda.is_available(),
    dataloader_num_workers=4,
    logging_steps=100,

    # 可复现
    seed=42,
    report_to='none',       # 不使用 wandb 等在线服务
)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()
trainer.save_model('./best_model')
tokenizer.save_pretrained('./best_model')
```

### 自定义训练循环

当 Trainer 无法满足需求时（如自定义 loss、多任务学习、GAN 训练），手动编写训练循环：

```python
def train_one_epoch(model, dataloader, optimizer, loss_fn, device, epoch):
    """训练一个epoch"""
    model.train()
    total_loss = 0.0
    progress_bar = tqdm(dataloader, desc=f'Epoch {epoch}')

    for batch in progress_bar:
        optimizer.zero_grad()
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        progress_bar.set_postfix({'loss': f'{loss.item():.4f}'})

    return total_loss / len(dataloader)

@torch.no_grad()
def evaluate(model, dataloader, device):
    """评估模型"""
    model.eval()
    total_loss = 0.0
    correct, total = 0, 0

    for batch in tqdm(dataloader, desc='Evaluating'):
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)

        total_loss += outputs.loss.item()
        preds = outputs.logits.argmax(dim=-1)
        correct += (preds == batch['labels']).sum().item()
        total += batch['labels'].size(0)

    acc = correct / total
    return total_loss / len(dataloader), acc
```

### 混合精度与分布式

使用 `accelerate` 或 `torch.cuda.amp` 进行混合精度训练：

```python
# 使用 accelerate（推荐）
from accelerate import Accelerator

accelerator = Accelerator(mixed_precision='fp16')
model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

# 训练时用 accelerator.backward(loss) 替代 loss.backward()
```

### 打印输出格式

无论使用 Trainer 还是自定义循环，关键信息集中在一行：

```python
# Correct:
print(f'Epoch {epoch}/{num_epochs} | '
      f'train_loss: {train_loss:.4f} | train_acc: {train_acc:.4f} | '
      f'eval_loss: {eval_loss:.4f} | eval_acc: {eval_acc:.4f}')
```

epoch 计数始终从 1 开始。使用 f-string 格式化，拒绝逗号分隔的 print。

---

## 数据处理

数据加载与预处理优先使用 `datasets` 库。

### 加载数据

从 HuggingFace Hub 或本地文件加载：

```python
from datasets import load_dataset, Dataset, DatasetDict

# 从 Hub 加载
dataset = load_dataset('imdb')

# 从本地文件加载
dataset = load_dataset('csv', data_files='data/train.csv')
dataset = load_dataset('json', data_files='data/train.json')

# 只加载指定划分
train_dataset = load_dataset('imdb', split='train')
small_train = load_dataset('imdb', split='train[:10%]')   # 前10%

# 超大数据集使用流式模式
dataset = load_dataset('c4', 'en', split='train', streaming=True)
```

### 数据集划分

```python
# HuggingFace 数据集通常自带 train/test/validation 划分
print(dataset)  # DatasetDict with keys: ['train', 'test', 'unsupervised']

# 从 train 中切出验证集
split_dataset = dataset['train'].train_test_split(test_size=0.2, seed=42)
dataset = DatasetDict({
    'train': split_dataset['train'],
    'validation': split_dataset['test'],
    'test': dataset['test'],
})
```

### 数据预处理：map()

`map()` 是核心的数据转换方法。始终使用 `batched=True` 以获得更好的性能：

```python
def preprocess_function(examples):
    """分词并截断"""
    return tokenizer(
        examples['text'],
        truncation=True,
        max_length=512,
        # 不在 map 中 padding — 交给 DataCollatorWithPadding 动态处理
    )

tokenized_dataset = dataset.map(
    preprocess_function,
    batched=True,
    num_proc=4,                          # 多进程加速
    remove_columns=dataset['train'].column_names,  # 只保留分词结果
)
```

不要预先 padding 整个数据集。在 map 中去掉原始文本列，由 `DataCollatorWithPadding` 在构造 batch 时动态 padding：

```python
# Correct — 微调时动态 padding
from transformers import DataCollatorWithPadding

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Wrong — 预 padding 浪费大量内存
def tokenize(examples):
    return tokenizer(examples['text'], padding='max_length', max_length=512)
```

### 数据筛选：filter()

```python
# 按条件筛选样本
long_reviews = dataset.filter(lambda x: len(x['text']) > 100)

# 带索引筛选
even_samples = dataset.filter(lambda x, idx: idx % 2 == 0, with_indices=True)

# 多进程筛选
dataset = dataset.filter(condition_fn, num_proc=4)
```

### 格式设置：set_format()

```python
# 转换为 PyTorch 张量
tokenized_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

# 重置为 Python 对象
tokenized_dataset.reset_format()
```

### 保存与缓存

预处理后的数据集缓存到磁盘，避免重复计算：

```python
# 自动缓存（map 默认行为，需指定缓存路径）
tokenized_dataset = dataset.map(preprocess_function, batched=True,
                                cache_file_name='cache/tokenized.arrow')

# 显式保存
tokenized_dataset.save_to_disk('cache/tokenized_dataset')

# 加载
from datasets import load_from_disk
tokenized_dataset = load_from_disk('cache/tokenized_dataset')
```

### 完整预处理流水线示例

```python
from datasets import load_dataset, DatasetDict
from transformers import AutoTokenizer, DataCollatorWithPadding

# 1. 加载
dataset = load_dataset('imdb')

# 2. 划分验证集
split = dataset['train'].train_test_split(test_size=0.2, seed=42)
dataset = DatasetDict({
    'train': split['train'],
    'validation': split['test'],
    'test': dataset['test'],
})

# 3. 分词
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

def tokenize_fn(examples):
    return tokenizer(examples['text'], truncation=True, max_length=512)

tokenized_dataset = dataset.map(
    tokenize_fn,
    batched=True,
    num_proc=4,
    remove_columns=['text'],
)

# 4. 数据整理器（动态 padding）
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 5. 送入 Trainer 或 DataLoader
```

---

## 数学符号与形状注释

### 形状注释格式

张量形状说明使用英文半角标点，括号内逗号后跟空格：

```python
# Correct:
# X的形状：(批量大小, 词数)
# queries的形状：(batch_size, 查询的个数, num_hiddens)

# Wrong:
# X的形状：（批量大小，词数）
```

### 形状变换注释

每次形状变换操作附带注释说明变换后的维度：

```python
# 输出X的形状:(batch_size,查询的个数,num_heads,num_hiddens/num_heads)
X = X.reshape(X.shape[0], X.shape[1], num_heads, -1)

# 最终输出的形状:(batch_size*num_heads,查询的个数,num_hiddens/num_heads)
return X.reshape(-1, X.shape[2], X.shape[3])
```

### 公式引用

代码注释中引用公式使用 LaTeX 符号：

```python
# Correct:
# 计算 softmax: exp(o_j) / sum_k exp(o_k)
# 损失函数: (y_hat - y)^2 / 2
```

---

## 术语约定

### 中英文对照

以下术语全书统一使用。首次出现时附注英文原文（不加粗，不加引号）：

| 中文 | 英文 |
|------|------|
| 模型训练 | model training |
| 模型预测/推断 | model prediction / inference |
| 训练数据集 | training dataset |
| 验证数据集 | validation dataset |
| 测试数据集 | test dataset |
| 超参数 | hyperparameter |
| 权重 | weight |
| 偏置 | bias |
| 标签 | label |
| 特征 | feature |
| 损失函数 | loss function |
| 优化器 | optimizer |
| 迭代周期 | epoch |
| 批量 | batch |
| 小批量 | minibatch |
| 学习率 | learning rate |
| 准确率/精度 | accuracy |
| 过拟合 | overfitting |
| 欠拟合 | underfitting |
| 泛化 | generalization |
| 暂退法 | dropout |
| 梯度裁剪 | gradient clipping |
| 层 | layer |
| 全连接层 | fully-connected layer |
| 卷积神经网络 | convolutional neural network |
| 循环神经网络 | recurrent neural network |
| 注意力机制 | attention mechanism |
| 编码器 | encoder |
| 解码器 | decoder |
| 自注意力 | self-attention |
| 多头注意力 | multi-head attention |
| 词元 | token |
| 词表 | vocabulary |
| 词嵌入 | word embedding |
| 隐藏层 | hidden layer |
| 隐藏单元 | hidden unit |
| 激活函数 | activation function |
| 规范化 | normalization |
| 汇聚层 | pooling layer |
| 填充 | padding |
| 步幅 | stride |
| 通道 | channel |
| 实例 | instance（不称"对象"） |
| 函数 | function（不称"方法"） |
| 分词器 | tokenizer |
| 预训练模型 | pretrained model |
| 微调 | fine-tuning |
| 适配器 | adapter / PEFT |
| 推理 | inference |
| 检查点 | checkpoint |
| 数据整理器 | data collator |
| 流式加载 | streaming |
| 动态填充 | dynamic padding |

---

## 编程建议

### tokenizer 使用规范

调用 tokenizer 时始终显式指定关键参数：

```python
# Correct:
tokens = tokenizer(
    texts,
    truncation=True,            # 超出长度则截断
    max_length=512,             # 显式指定最大长度
    return_tensors='pt',        # 返回 PyTorch 张量
)

# Avoid — 依赖默认行为：
tokens = tokenizer(texts)
```

### 梯度管理

- 训练：`optimizer.zero_grad()` → `loss.backward()` → `optimizer.step()`
- 评估：必须置于 `with torch.no_grad():` 内
- 使用 `accelerator.backward(loss)` 替代 `loss.backward()` 以获得混合精度支持

### 显式设备管理

```python
# Correct — 显式迁移到设备：
model.to(device)
batch = {k: v.to(device) for k, v in batch.items()}
```

使用 `device_map='auto'` 的大模型不要手动调用 `.to()`。

### 可复现性

```python
SEED = 42
torch.manual_seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

# TrainingArguments 中也设置
TrainingArguments(..., seed=SEED)
```

### 浮点数字面量

```python
# Correct:
x = 1.0
y = 0.0

# Wrong:
x = 1.
y = .1
```

### 显存优化与量化

大模型加载时优先使用 bitsandbytes 量化。NLU 任务用 INT8，生成式 LLM 用 NF4 + QLoRA：

#### INT8 量化（适用于 BERT 类判别式模型）

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map='auto',
)
```

#### 4-bit NF4 量化 + QLoRA（适用于 Llama/Qwen 等生成式模型）

```python
import torch
from transformers import BitsAndBytesConfig, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 4-bit 量化配置
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',              # NormalFloat4（对正态分布权重最优）
    bnb_4bit_use_double_quant=True,         # 嵌套量化（每参数节省约0.4 bit）
    bnb_4bit_compute_dtype=torch.bfloat16,  # 计算精度（A100用bfloat16，V100用float16）
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map='auto',
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

# 为 k-bit 训练做准备
model = prepare_model_for_kbit_training(model)

# 配置 LoRA
peft_config = LoraConfig(
    r=8,
    lora_alpha=16,                # 通常设为 2 * r
    target_modules='all-linear',  # 或手动指定：['q_proj','k_proj','v_proj','o_proj']
    lora_dropout=0.05,
    bias='none',
    task_type='CAUSAL_LM',
)

model = get_peft_model(model, peft_config)
model.print_trainable_parameters()
# 输出示例: trainable params: 4.2M || all params: 6.7B || trainable%: 0.06%

# 训练开始前必须禁用 KV 缓存
model.config.use_cache = False
```

#### 量化选择速查

| 量化方案 | 每参数显存 | 适用场景 |
|----------|----------|----------|
| 无量化 (FP16) | 2 bytes | 小模型（<1B）完整微调 |
| INT8 | ~1 byte | BERT/RoBERTa 微调，精度接近 FP16 |
| NF4 + 双重量化 | ~0.5 bytes | 7B+ 模型 QLoRA 微调，单卡可跑 13B |
| 8-bit AdamW | optimizer 省 75% | 全参数训练的优化器替换 |

#### 训练注意事项

- QLoRA 训练时 `TrainingArguments` 中必须设置 `fp16=True`（非 bf16）；
- 训练前 `model.config.use_cache = False`；
- 保存时只存 adapter 权重：`model.save_pretrained('./adapter')`，不存完整的量化基座模型；
- 如果通过 HuggingFace Hub 无法下载模型，设置 `HF_ENDPOINT=https://hf-mirror.com` 环境变量。

### 推理

简单任务用 `pipeline`，复杂逻辑手写循环：

```python
from transformers import pipeline

classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
results = classifier(['This is great!', 'I hated it.'])

# 复杂任务手写
model.eval()
with torch.no_grad():
    for batch in dataloader:
        ...
```

---

## 参考资料

本规范编写过程中参考了以下项目与文档：

| 库/文档 | 用途 |
|---------|------|
| [PEP 8](https://peps.python.org/pep-0008/) | Python 代码风格基线 |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring 约定 |
| [Dive into Deep Learning](https://d2l.ai) | 编码风格与术语对照参考 |
| [accelerate](https://huggingface.co/docs/accelerate) | 分布式训练与混合精度 |
| [bitsandbytes](https://huggingface.co/docs/bitsandbytes) | 模型量化（INT8/NF4） |
| [datasets](https://huggingface.co/docs/datasets) | 数据加载与预处理 |
| [huggingface-hub](https://huggingface.co/docs/huggingface_hub) | 模型与数据集托管 |
| [matplotlib](https://matplotlib.org) | 可视化 |
| [numpy](https://numpy.org) | 数值计算 |
| [peft](https://huggingface.co/docs/peft) | 参数高效微调（LoRA/QLoRA） |
| [torch](https://pytorch.org/docs) | 深度学习框架 |
| [transformers](https://huggingface.co/docs/transformers) | 预训练模型与训练工具 |
