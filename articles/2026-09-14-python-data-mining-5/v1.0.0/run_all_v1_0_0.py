"""v1.0.0 | 重新生成全部模拟数据、运行五个案例、输出实际结果。"""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import make_data_v1_0_0 as data
import case01_regression_v1_0_0 as reg
import case02_logistic_v1_0_0 as logit
import case03_tree_v1_0_0 as tree
import case04_kmeans_v1_0_0 as cluster
import case05_association_v1_0_0 as association
from common_v1_0_0 import result
import platform,importlib.metadata

if __name__=='__main__':
    data.main()
    for module in [reg,logit,tree,cluster,association]:
        print('\nRUN',module.__name__,flush=True);module.main()
    result('environment',{'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ['numpy','pandas','matplotlib','scikit-learn','mlxtend']}})
