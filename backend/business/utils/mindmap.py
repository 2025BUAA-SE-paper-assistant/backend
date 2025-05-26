import subprocess
import os
import tempfile

def mermaid_to_image(mermaid_code: str, output_path: str) -> str:
    # 保存 mermaid 代码到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as mmd_file:
        mmd_file.write(mermaid_code)
        mmd_file_path = mmd_file.name

    # 调用 mermaid-cli 生成图片
    try:
        subprocess.run([
            'mmdc',
            '-i', mmd_file_path,
            '-o', output_path,
            '--puppeteerConfigFile', '/usr/zjq/backend/backend/business/utils/puppeteer-config.json'  # 加这一行
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Mermaid CLI 生成图片失败: {e}")
    finally:
        os.remove(mmd_file_path)

    return os.path.abspath(output_path)

# 示例使用
if __name__ == '__main__':
    mermaid_code = """
    graph TD
        A[开始] --> B{条件判断}
        B -->|是| C[处理过程1]
        B -->|否| D[处理过程2]
        C --> E[结束]
        D --> E
    """
    output_file = 'output.png'
    local_path = mermaid_to_image(mermaid_code, output_file)
    print(f"生成的图片保存在：{local_path}")
