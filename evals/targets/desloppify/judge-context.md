# Desloppify Judge Context

## What Counts as Slop

**Code comment slop:**
- Narrator comments ("Now we process the data")
- Obvious comments that restate the code (`x += 1 # Increment x`)
- Defensive error handling for impossible cases
- Single-use constants extracted for no reason
- Apologetic comments ("This might not be the best approach")
- Redundant type documentation that repeats what the type signature says

**Prose slop:**
- Filler phrases: "It's worth noting", "Interestingly", "As mentioned"
- AI vocabulary: "robust", "leverage", "seamlessly", "comprehensive", "cutting-edge"
- Promotional adjectives: "powerful", "elegant", "state-of-the-art"
- Restating what was just said in different words

## What Is NOT Slop

- Comments explaining *why* (business logic, non-obvious decisions)
- TODO/FIXME/HACK comments with context
- Legal/license headers
- API documentation that adds information beyond the type signature
- Error messages with actionable detail
- Comments referencing external systems, tickets, or constraints

## Ground Truth Per Prompt

### Prompt 01 (python-slop): 8 planted slop patterns
1. Module docstring full of filler ("robust", "comprehensive", "leverages")
2. Function docstring restates function name with buzzwords
3. Inline comment `# Increment counter` on `counter += 1`
4. Inline comment `# Return the result` on `return result`
5. Try-catch around infallible dict access with apologetic comment
6. Single-use constant `MAGIC_OFFSET = 1` used once
7. Section divider `# ============= MAIN LOGIC =============`
8. Narrator comment "Now we initialize the database connection"

### Prompt 02 (typescript-clean): Zero slop
- 3 legitimate comments explaining business logic
- Clean, well-typed code
- Expected result: "no slop found" or equivalent

### Prompt 03 (markdown-prose): 6 planted prose slop patterns
1. "It's worth noting that this configuration..."
2. "This robust and comprehensive solution..."
3. "Leveraging the power of modern tooling..."
4. "Seamlessly integrates with existing workflows"
5. "Provides a streamlined and performant experience"
6. Paragraph that restates the previous paragraph in different words

### Prompt 04 (mixed-legitimate): 3 slop + 3 legitimate
- 3 obvious comments (slop) mixed with 3 why-comments (legitimate)
- The skill must catch the slop WITHOUT flagging the legitimate comments
- This is the false-positive resistance test

### Prompt 05 (edge-case-defensive): 2 slop + 1 justified
- 2 defensive try-catches that are unjustified (slop)
- 1 defensive try-catch that IS justified (external API call that can fail)
- The skill must distinguish between unnecessary and justified defensive code
