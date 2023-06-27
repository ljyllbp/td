# td工具

## td工具介绍
td命令行工具为方便针对标注平台数据上传、下载的本地命令行工具，在较大数据量时，浏览器上传下载受限时可用命令行工具操作更高效。
支持Mac（Arm构架和Intel构架）、Linux、Windows系统。

## 下载地址
下载成功解压后将解压得到的目录路径加入到本地的环境变量中，可在命令行终端中直接使用td命令，或者通过完整路径执行td命令。

当前版本：0.1.0
sudo spctl --master-disable

[Linux版本](http://src1-yscdn.testin.cn/data/td/0.1.0/td_linux.zip)  
[Mac-Arm版本](http://src1-yscdn.testin.cn/data/td/0.1.0/td_mac_arm.zip)  
[Mac-Intel版本](http://src1-yscdn.testin.cn/data/td/0.1.0/td_mac_amd.zip)  
[Windows版本](http://src1-yscdn.testin.cn/data/td/0.1.0/td_win.zip)

## 命令介绍

### upload
td upload <ds_id> <ak> <data_root> [flags]

**功能**
上传数据至平台，并进行如下检查

- 检查目录名以及文件名是否属于utf-8字符集
- 检查目录名以及文件名是否含有'?', '#', ':', '%'内的特殊字符
- 检查目录是否符合数据集目录格式要求
- 检查图像，序列图像，点云预标注结果文件id

**必选字段**

|字段名|类型|说明|
|:-:|:-:|:-:|
|ds_id|string|平台数据集id|
|ak|string|平台创建数据集账号的密钥|
|data_root|string|符合数据集格式要求的数据目录|

**可选字段**

|字段名|简写|默认值|类型|说明|
|:-:|:-:|:-:|:-:|:-:|
|force_compressed|f|false|bool|是否强制压缩点云|
|help|h|||说明|
|host||http://label-std.testin.cn|string|平台的host|
|retry_count|r|10|int|每个文件上传失败后重传次数|
|simplify_pcd|s|false|bool|是否精简点云|
|thread_num|t|cpu 个数|int|上传文件并发数|

**示例**
```
td upload ds_8hbhpcp5ifqdbm6fr5jo 95c6f35e29bbd0621d2a0ef2c8846adee86c /data/点云
td upload ds_8hbhpcp5ifqdbm6fr5jo 95c6f35e29bbd0621d2a0ef2c8846adee86c /data/点云 -s -f --host http://label-std.testin.cn -r 10 -t 10
td upload ds_8hbhpcp5ifqdbm6fr5jo 95c6f35e29bbd0621d2a0ef2c8846adee86c /data/点云 --simplify_pcd --force_compressed --host http://label-std.testin.cn --retry_count 10 --thread_num 10
```

### export
td export <task_batch_key> <ak> <out> [flags]

**功能**

从任务key下载数据至本地

**必选字段**

|字段名|类型|说明|
|:-:|:-:|:-:|
|task_batch_key|string|平台任务key|
|ak|string|平台创建数据集账号的密钥|
|out|string|保存数据的目录|

**可选字段**

|字段名|简写|默认值|类型|说明|
|:-:|:-:|:-:|:-:|:-:|
|download_type|d|label|string|下载类型:label, original 或 original_and_label|
|have_more_info|m|false|bool|标注结果文件是否包含角色信息|
|help|h|||说明|
|host||http://label-std.testin.cn|string|平台的host|
|operate_work_type||none|int|操作工序|
|operate_users||none|int|操作员id|
|package_id|p|none|int|题id|
|retry_count|r|10|int|每个文件下载失败后重试次数|
|seg_dir_name||none|string|序列名称|
|status|s|99|int|题状态|
|task_id|t|none|int|子题id|
|thread_num|n|cpu 个数|int|下载文件并发数|
|work_type|w|1|int|工序|

**工序id对应表**
|id|状态|
|:-:|:-:|
|1|标注|
|2|审核|
|3|质检|
|4|验收|

**题状态id对应表**
|id|状态|
|:-:|:-:|
|0|待处理|
|1|进行中|
|2|已通过|
|3|已驳回|
|99|全部|

**示例**
```
td export 230619ad96c 95c6f35e29bbd0621d2a0ef2c8846adee86c /out
td export 230619ad96c 95c6f35e29bbd0621d2a0ef2c8846adee86c /out -d label -f 000.pcd -m --host http://label-std.testin.cn --operate_work_type 1 --operate_users 129 -p 1031110 -r 10 --seg_dir_name segment_000 -s 99 -t 2794732  -n 10 -w 1
td export 230619ad96c 95c6f35e29bbd0621d2a0ef2c8846adee86c /out --download_type label --file_name 000.pcd --have_more_info --host http://label-std.testin.cn --operate_work_type 1 --operate_users 129 --package_id 1031110 --retry_count 10 --seg_dir_name segment_000 --status 99 --task_id 2794732  --thread_num 10 --work_type 1
```

## 可能遇到的问题

**mac**
```
因为Apple无法检查其是否包含恶意软件
系统偏好->安全性与隐私->通用->勾选'任何来源'
若无'任何来源'选项
终端输入 sudo spctl --master-enable
输入密码
系统偏好->安全性与隐私->通用->勾选'任何来源'
```
