"""ZeroLINC: training-free local classification of security incident tickets.

Two engines share the CLI and the ``router`` entry point: the instance-memory
engine (``memory_engine``), which votes over previously labeled tickets and
backs Claim #1 (90.8% mean accuracy from 89 references, no gradient
training), and the zero-shot engines (``zeroshot_engine``), which need no
labeled data and back Claim #2 (up to 70.9%, 68.8% under the selection
protocol) and Claim #3 (the default engine classifies the corpus in seconds
and under 3 Wh). No model weights are ever updated by this package.
"""
