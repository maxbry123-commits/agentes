/**
 * Command Tokenizer - Parses shell commands into structured tokens
 */

import * as path from 'path';
import * as os from 'os';
import { ParsedCommand, Token, CommandSegment } from './types';

export class CommandTokenizer {
  private readonly ESCAPED_SPACE_PLACEHOLDER = '\x00ESCAPED_SPACE\x00';

  tokenize(command: string): ParsedCommand {
    const original = command;
    
    // Step 1: Handle escape sequences (use placeholder for escaped spaces)
    const escapedCommand = this.handleEscapes(command);
    
    // Step 2: Parse into tokens while respecting quotes
    const tokens = this.handleQuotes(escapedCommand);
    
    // Step 3: Restore escaped spaces and expand variables/paths in tokens
    const expandedTokens = tokens.map(token => ({
      ...token,
      value: this.expandPaths(this.expandVariables(
        token.value.replace(new RegExp(this.ESCAPED_SPACE_PLACEHOLDER, 'g'), ' ')
      ))
    }));
    
    // Step 4: Build normalized command string
    const normalized = expandedTokens.map(t => t.value).join(' ');
    
    // Step 5: Split into command segments (for chained/piped commands)
    const segments = this.splitSegments(expandedTokens);
    
    // Step 6: Determine if command is chained or piped
    const isChained = expandedTokens.some(t => 
      t.type === 'operator' && ['&&', '||', ';'].includes(t.value)
    );
    const isPiped = expandedTokens.some(t => 
      t.type === 'operator' && t.value === '|'
    );
    
    return {
      original,
      normalized,
      tokens: expandedTokens,
      segments,
      isChained,
      isPiped
    };
  }

  private expandVariables(token: string): string {
    // Expand environment variables: $VAR and ${VAR}
    let expanded = token;
    
    // Handle ${VAR} format
    expanded = expanded.replace(/\$\{([^}]+)\}/g, (match, varName) => {
      return process.env[varName] || match;
    });
    
    // Handle $VAR format (word boundary aware)
    expanded = expanded.replace(/\$([A-Za-z_][A-Za-z0-9_]*)/g, (match, varName) => {
      return process.env[varName] || match;
    });
    
    return expanded;
  }

  private expandPaths(token: string): string {
    // Expand tilde to home directory
    if (token.startsWith('~/')) {
      return path.join(os.homedir(), token.slice(2));
    }
    if (token === '~') {
      return os.homedir();
    }
    
    // Resolve relative paths to absolute paths
    // Only resolve if it looks like a path (starts with ./ or ../)
    if (token.startsWith('./') || token.startsWith('../')) {
      return path.resolve(token);
    }
    
    return token;
  }

  private handleQuotes(command: string): Token[] {
    const tokens: Token[] = [];
    let currentToken = '';
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let position = 0;
    let tokenStart = 0;
    let isFirstToken = true;
    
    for (let i = 0; i < command.length; i++) {
      const char = command[i];
      const nextChar = i + 1 < command.length ? command[i + 1] : '';
      
      if (char === "'" && !inDoubleQuote) {
        inSingleQuote = !inSingleQuote;
        currentToken += char;
      } else if (char === '"' && !inSingleQuote) {
        inDoubleQuote = !inDoubleQuote;
        currentToken += char;
      } else if (!inSingleQuote && !inDoubleQuote) {
        // Check for multi-character operators outside quotes
        if (char === '&' && nextChar === '&') {
          // Save current token if any
          if (currentToken.length > 0) {
            tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
            isFirstToken = false;
            currentToken = '';
          }
          // Add && operator
          tokens.push(this.createToken('&&', i, false));
          i++; // Skip next character
          tokenStart = i + 1;
        } else if (char === '|' && nextChar === '|') {
          // Save current token if any
          if (currentToken.length > 0) {
            tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
            isFirstToken = false;
            currentToken = '';
          }
          // Add || operator
          tokens.push(this.createToken('||', i, false));
          i++; // Skip next character
          tokenStart = i + 1;
        } else if (char === '|' && nextChar !== '|') {
          // Single pipe (not ||)
          if (currentToken.length > 0) {
            tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
            isFirstToken = false;
            currentToken = '';
          }
          // Add | operator
          tokens.push(this.createToken('|', i, false));
          tokenStart = i + 1;
        } else if (char === ';') {
          // Semicolon separator
          if (currentToken.length > 0) {
            tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
            isFirstToken = false;
            currentToken = '';
          }
          // Add ; operator
          tokens.push(this.createToken(';', i, false));
          tokenStart = i + 1;
        } else if (char === ' ') {
          // Space outside quotes - token boundary
          if (currentToken.length > 0) {
            tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
            isFirstToken = false;
            currentToken = '';
          }
          tokenStart = i + 1;
        } else {
          currentToken += char;
        }
      } else {
        currentToken += char;
      }
    }
    
    // Add final token
    if (currentToken.length > 0) {
      tokens.push(this.createToken(currentToken, tokenStart, isFirstToken));
    }
    
    return tokens;
  }

  private createToken(tokenStr: string, position: number, isFirst: boolean): Token {
    const originalValue = tokenStr;
    
    // Remove surrounding quotes but preserve the content
    let value = tokenStr;
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    
    // Determine token type
    let type: Token['type'];
    // Check for operators first (before removing quotes)
    if (['&&', '||', ';', '|'].includes(tokenStr)) {
      type = 'operator';
    } else if (['>', '>>'].includes(tokenStr)) {
      type = 'redirect';
    } else if (isFirst && !['&&', '||', ';', '|', '>', '>>'].includes(tokenStr)) {
      type = 'command';
    } else {
      type = 'argument';
    }
    
    return {
      type,
      value,
      originalValue,
      position
    };
  }

  private handleEscapes(command: string): string {
    // Handle escape sequences: \, \", \', and escaped spaces
    let result = '';
    let i = 0;
    
    while (i < command.length) {
      if (command[i] === '\\' && i + 1 < command.length) {
        const nextChar = command[i + 1];
        // Handle common escape sequences
        if (nextChar === '\\' || nextChar === '"' || nextChar === "'") {
          result += nextChar;
          i += 2;
        } else if (nextChar === ' ') {
          // Use placeholder for escaped space to prevent tokenization split
          result += this.ESCAPED_SPACE_PLACEHOLDER;
          i += 2;
        } else {
          // Unknown escape sequence - preserve both characters
          result += command[i];
          i++;
        }
      } else {
        result += command[i];
        i++;
      }
    }
    
    return result;
  }

  private splitSegments(tokens: Token[]): CommandSegment[] {
    const segments: CommandSegment[] = [];
    let currentCommand = '';
    let currentArgs: string[] = [];
    let isFirstTokenInSegment = true;
    
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];
      
      if (token.type === 'operator') {
        // Save current segment with the operator
        if (currentCommand) {
          segments.push({
            command: currentCommand,
            args: currentArgs,
            operator: token.value as CommandSegment['operator']
          });
        }
        
        // Reset for next segment
        currentCommand = '';
        currentArgs = [];
        isFirstTokenInSegment = true;
      } else if (isFirstTokenInSegment && (token.type === 'command' || token.type === 'argument')) {
        // First non-operator token in a segment becomes the command
        currentCommand = token.value;
        isFirstTokenInSegment = false;
      } else if (token.type === 'argument') {
        currentArgs.push(token.value);
      }
    }
    
    // Add final segment (without operator)
    if (currentCommand) {
      segments.push({
        command: currentCommand,
        args: currentArgs,
        operator: undefined
      });
    }
    
    return segments;
  }
}
