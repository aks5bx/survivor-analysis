#!/usr/bin/env python3
"""
Train an XGBoost model to predict player elimination at tribal council.

Features proper cross-validation, hyperparameter tuning, and evaluation metrics.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, 
    precision_recall_curve, average_precision_score, roc_curve
)
import xgboost as xgb
import matplotlib.pyplot as plt
from pathlib import Path
import joblib
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = "../../docs/data"
OUTPUT_DIR = "../../models"

def load_and_prepare_data(filepath):
    """Load data and prepare features for modeling."""
    print("Loading data...")
    df = pd.read_csv(filepath)
    
    print(f"Total rows: {len(df)}")
    print(f"Elimination rate: {df['eliminated'].mean()*100:.1f}%")
    
    # Define feature columns
    identifier_cols = ['episode', 'castaway_id', 'castaway', 'tribe']
    target_col = 'eliminated'
    
    feature_cols = [
        # Season (as requested)
        'season',
        
        # Confessional features
        'confessionals_prev_ep',
        'confessionals_last_2_ep',
        'confessionals_last_3_ep',
        'confessionals_cumulative',
        'confessional_time_prev_ep',
        'confessional_time_last_2_ep',
        'confessional_time_last_3_ep',
        'confessional_time_cumulative',
        
        # Vote features
        'votes_against_prev_ep',
        'votes_against_last_2_ep',
        'votes_against_last_3_ep',
        'votes_against_cumulative',
        'times_received_votes',
        
        # Voting accuracy features
        'voting_accuracy_prev_ep',
        'voting_accuracy_last_2_ep',
        'voting_accuracy_last_3_ep',
        'voting_accuracy_cumulative',
        
        # Challenge features
        'individual_wins_prev_ep',
        'individual_wins_last_2_ep',
        'individual_wins_last_3_ep',
        'individual_wins_cumulative',
        
        # Tribe features
        'num_tribe_swaps',
        
        # Advantage features
        'has_idol',
        'has_extra_vote',
        'has_steal_vote',
        'has_block_vote',
        'has_idol_nullifier',
        'has_other_advantage',
        'advantages_in_circulation',
        
        # Game state
        'players_remaining',
        'day',
        
        # Demographics
        'gender',
        'age',
        'age_bucket',
        'race_cat',
        'collar',
        'personality_type',
    ]
    
    # Prepare features
    X = df[feature_cols].copy()
    y = df[target_col].astype(int)
    
    # Encode categorical variables
    categorical_cols = ['gender', 'age_bucket', 'race_cat', 'collar', 'personality_type']
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        # Handle NaN by converting to string first
        X[col] = X[col].fillna('Unknown').astype(str)
        X[col] = le.fit_transform(X[col])
        label_encoders[col] = le
    
    # Convert boolean columns to int
    bool_cols = ['has_idol', 'has_extra_vote', 'has_steal_vote', 'has_block_vote', 
                 'has_idol_nullifier', 'has_other_advantage']
    for col in bool_cols:
        X[col] = X[col].astype(int)
    
    # Fill any remaining NaN with median
    X = X.fillna(X.median())
    
    print(f"Features: {len(feature_cols)}")
    print(f"Categorical encoded: {categorical_cols}")
    
    return X, y, df, label_encoders, feature_cols


def train_with_cv(X, y, n_splits=5):
    """Train XGBoost with cross-validation."""
    print(f"\n{'='*50}")
    print(f"Training with {n_splits}-fold Stratified Cross-Validation")
    print('='*50)
    
    # Define base model with class imbalance handling
    scale_pos_weight = (y == 0).sum() / (y == 1).sum()
    print(f"Scale pos weight (for class imbalance): {scale_pos_weight:.2f}")
    
    base_model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='auc',
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1
    )
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1],
        'min_child_weight': [1, 3],
        'subsample': [0.8],
        'colsample_bytree': [0.8],
    }
    
    # Stratified K-Fold
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    print("\nPerforming GridSearchCV for hyperparameter tuning...")
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=cv,
        scoring='roc_auc',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    print(f"\nBest parameters: {grid_search.best_params_}")
    print(f"Best CV AUC: {grid_search.best_score_:.4f}")
    
    best_model = grid_search.best_estimator_
    
    # Get cross-validated predictions for evaluation
    print("\nGenerating cross-validated predictions...")
    y_pred_proba = cross_val_predict(best_model, X, y, cv=cv, method='predict_proba')[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    return best_model, y_pred, y_pred_proba, grid_search.best_params_


def evaluate_model(y_true, y_pred, y_pred_proba):
    """Comprehensive model evaluation."""
    print(f"\n{'='*50}")
    print("Model Evaluation (Cross-Validated)")
    print('='*50)
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=['Not Eliminated', 'Eliminated']))
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print("\nConfusion Matrix:")
    print(cm)
    
    # AUC-ROC
    auc_roc = roc_auc_score(y_true, y_pred_proba)
    print(f"\nAUC-ROC: {auc_roc:.4f}")
    
    # Average Precision (AUC-PR)
    avg_precision = average_precision_score(y_true, y_pred_proba)
    print(f"Average Precision (AUC-PR): {avg_precision:.4f}")
    
    # At different thresholds
    print("\nPerformance at different probability thresholds:")
    for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
        y_pred_t = (y_pred_proba >= threshold).astype(int)
        tp = ((y_pred_t == 1) & (y_true == 1)).sum()
        fp = ((y_pred_t == 1) & (y_true == 0)).sum()
        fn = ((y_pred_t == 0) & (y_true == 1)).sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        print(f"  Threshold {threshold}: Precision={precision:.3f}, Recall={recall:.3f}")
    
    return auc_roc, avg_precision


def plot_results(y_true, y_pred_proba, feature_importances, feature_names, output_dir):
    """Generate evaluation plots."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. ROC Curve
    ax1 = axes[0, 0]
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)
    ax1.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
    ax1.plot([0, 1], [0, 1], 'k--', label='Random')
    ax1.set_xlabel('False Positive Rate')
    ax1.set_ylabel('True Positive Rate')
    ax1.set_title('ROC Curve')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Precision-Recall Curve
    ax2 = axes[0, 1]
    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    avg_precision = average_precision_score(y_true, y_pred_proba)
    ax2.plot(recall, precision, label=f'PR Curve (AP = {avg_precision:.3f})')
    ax2.axhline(y=y_true.mean(), color='k', linestyle='--', label=f'Baseline ({y_true.mean():.3f})')
    ax2.set_xlabel('Recall')
    ax2.set_ylabel('Precision')
    ax2.set_title('Precision-Recall Curve')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Feature Importance (Top 20) - if available
    ax3 = axes[1, 0]
    if feature_importances is not None and len(feature_importances) > 0:
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importances
        }).sort_values('importance', ascending=True).tail(20)
        
        ax3.barh(importance_df['feature'], importance_df['importance'])
        ax3.set_xlabel('Importance')
        ax3.set_title('Top 20 Feature Importances')
        ax3.grid(True, alpha=0.3, axis='x')
    else:
        ax3.text(0.5, 0.5, 'Feature importance not available', ha='center', va='center')
        ax3.set_title('Feature Importances')
    
    # 4. Prediction Distribution
    ax4 = axes[1, 1]
    ax4.hist(y_pred_proba[y_true == 0], bins=50, alpha=0.5, label='Not Eliminated', density=True)
    ax4.hist(y_pred_proba[y_true == 1], bins=50, alpha=0.5, label='Eliminated', density=True)
    ax4.set_xlabel('Predicted Probability')
    ax4.set_ylabel('Density')
    ax4.set_title('Prediction Distribution by Actual Outcome')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/elimination_model_evaluation.png', dpi=150)
    plt.close()
    print(f"\nPlots saved to {output_dir}/elimination_model_evaluation.png")


def analyze_feature_importance(model, feature_names):
    """Detailed feature importance analysis."""
    print(f"\n{'='*50}")
    print("Feature Importance Analysis")
    print('='*50)
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 15 Most Important Features:")
    for i, row in importance_df.head(15).iterrows():
        print(f"  {row['feature']:35s} {row['importance']:.4f}")
    
    print("\nFeature Importance by Category:")
    categories = {
        'Confessionals': [f for f in feature_names if 'confessional' in f],
        'Votes Against': [f for f in feature_names if 'votes_against' in f or 'times_received' in f],
        'Voting Accuracy': [f for f in feature_names if 'voting_accuracy' in f],
        'Challenges': [f for f in feature_names if 'win' in f],
        'Advantages': [f for f in feature_names if 'has_' in f or 'advantages_in' in f],
        'Game State': ['players_remaining', 'day', 'num_tribe_swaps', 'season'],
        'Demographics': ['gender', 'age', 'age_bucket', 'race_cat', 'collar', 'personality_type'],
    }
    
    for cat_name, cat_features in categories.items():
        cat_importance = importance_df[importance_df['feature'].isin(cat_features)]['importance'].sum()
        print(f"  {cat_name:20s} {cat_importance:.4f}")
    
    return importance_df


def main():
    # Load data
    data_path = f"{DATA_DIR}/elimination_training_data.csv"
    X, y, df, label_encoders, feature_cols = load_and_prepare_data(data_path)
    
    # Train with cross-validation
    model, y_pred, y_pred_proba, best_params = train_with_cv(X, y, n_splits=5)
    
    # Evaluate
    auc_roc, avg_precision = evaluate_model(y, y_pred, y_pred_proba)
    
    # Feature importance
    importance_df = analyze_feature_importance(model, feature_cols)
    
    # Plot results
    plot_results(y, y_pred_proba, model.feature_importances_, feature_cols, OUTPUT_DIR)
    
    # Retrain on full data for final model
    print(f"\n{'='*50}")
    print("Training Final Model on Full Dataset")
    print('='*50)
    
    final_model = xgb.XGBClassifier(
        **best_params,
        objective='binary:logistic',
        eval_metric='auc',
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
        random_state=42,
        n_jobs=-1
    )
    final_model.fit(X, y)
    
    # Save model and artifacts
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    model_path = f"{OUTPUT_DIR}/elimination_model.joblib"
    joblib.dump({
        'model': final_model,
        'label_encoders': label_encoders,
        'feature_cols': feature_cols,
        'best_params': best_params,
        'cv_auc_roc': auc_roc,
        'cv_avg_precision': avg_precision,
    }, model_path)
    print(f"\nModel saved to {model_path}")
    
    # Save feature importance
    importance_df.to_csv(f"{OUTPUT_DIR}/feature_importance.csv", index=False)
    print(f"Feature importance saved to {OUTPUT_DIR}/feature_importance.csv")
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    print(f"Cross-Validated AUC-ROC: {auc_roc:.4f}")
    print(f"Cross-Validated Avg Precision: {avg_precision:.4f}")
    print(f"Best Parameters: {best_params}")
    print(f"\nTop 5 Features:")
    for _, row in importance_df.head(5).iterrows():
        print(f"  - {row['feature']}: {row['importance']:.4f}")


if __name__ == "__main__":
    main()