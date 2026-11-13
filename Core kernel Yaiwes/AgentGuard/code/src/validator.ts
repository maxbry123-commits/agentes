/**
 * Validator - Main validation orchestrator
 */

import { ValidationResult } from './types';
import { RuleParser } from './rule-parser';
import { CommandTokenizer } from './command-tokenizer';
import { PatternMatcher } from './pattern-matcher';
import { RuleEngine } from './rule-engine';

export class Validator {
  private ruleParser: RuleParser;
  private tokenizer: CommandTokenizer;
  private matcher: PatternMatcher;
  private engine: RuleEngine;

  constructor() {
    this.ruleParser = new RuleParser();
    this.tokenizer = new CommandTokenizer();
    this.matcher = new PatternMatcher();
    this.engine = new RuleEngine();
  }

  validate(command: string): ValidationResult {
    // Orchestrate validation pipeline
    const rules = this.ruleParser.loadAll();
    const parsed = this.tokenizer.tokenize(command);
    return this.engine.validate(parsed, rules);
  }
}
