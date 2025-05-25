我需要你对于文章摘要生成思维导图，下面是生成样例
graph TD
    A[Natural Language Navigation for Service Robots] --> B[Task Definition]
    A --> C[Challenges]
    A --> D[Proposed Solution]
    A --> E[Experimental Results]

    B --> B1["- Predict action sequence from NL instructions"]
    B --> B2["- Example: 'Walk out of bathroom to right stairs'"]

    C --> C1["- Environment exploration"]
    C --> C2["- Accurate path following"]
    C --> C3["- Language-vision relationship modeling"]

    D --> D1[CrossMap Transformer Network]
    D --> D2[Transformer-based Speaker]
    D --> D3[Double Back-Translation Model]

    D1 --> D11["- Encodes linguistic/visual features"]
    D1 --> D12["- Sequentially generates paths"]

    D2 --> D21["- Generates navigation instructions"]

    D3 --> D31["- Paths → Instructions"]
    D3 --> D32["- Instructions → Paths"]
    D3 --> D33["- Shared latent features"]

    E --> E1["- Improved instruction understanding"]
    E --> E2["- Enhanced instruction generation"]
