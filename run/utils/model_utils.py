""" Utility functions for setting up and running AF2 models. """

from alphafold.model import config
from alphafold.model import model
from alphafold.model import data

from alphafold.data import pipeline

import numpy as np
from typing import Tuple

def getModelNames(
        mode: str, use_ptm: bool = True, num_models: int = 5) -> Tuple[str]:

    if mode == 'monomer':
        key = 'monomer_ptm' if use_ptm else 'monomer'
    elif mode == 'multimer':
        key = 'multimer'

    model_names = config.MODEL_PRESETS[key]
    model_names = model_names[:num_models]

    return model_names


def getModelRunner(
        model_name: str, num_ensemble: int = 1,
        params_dir: str = './alphafold/data') -> model.RunModel:

    cfg = config.model_config(model_name)

    if 'monomer' in model_name:
        cfg.data.eval.num_ensemble = num_ensemble
    elif 'multimer' in model_name:
        cfg.model.num_ensemble_eval = num_ensemble

    params = data.get_model_haiku_params(model_name, params_dir)

    return model.RunModel(cfg, params)


def predictStructure(
        model_runner: model.RunModel, random_seed: int = 0,
        feature_dict: pipeline.FeatureDict, model_type: str
        ) -> Dict[str, np.ndarray]:

    processed_feature_dict = model_runner.process_features(
        feature_dict, random_seed=random_seed)

    prediction = model_runner.predict(
        processed_feature_dict, random_seed=random_seed)

    result = {}
    
    if 'predicted_aligned_error' in prediction:
        result['pae_output'] = (prediction['predicted_aligned_error'],
                                prediction['max_predicted_aligned_error'])

    result['ranking_confidence'] = prediction['ranking_confidence']
    result['plddt'] = prediction['plddt']
    result['structure_module'] = prediction['structure_model']

    final_atom_mask = prediction['structure_module']['final_atom_mask']
    b_factors = prediction['plddts'][:, None] * final_atom_mask
    result['unrelaxed_protein'] = protein.from_prediction(
        processed_feature_dict,
        prediction,
        b_factors=b_factors,
        remove_leading_feature_dimension=(
            model_type == 'monomer'))
    
    return result