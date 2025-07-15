# Create git worktrees

READ the `Variables` then process the `RUN` commands then `report` the results.

## Variables

comma_separated_branch_names: $ARGUMENTS
tree_directory: `trees/`

## Run

For each branch name in `comma_separated_branch_names`, create a new git worktree in the `tree_directory` with the respective branch name.

Look for the .env in the root directoryh and copy it to the worktree directoryh for each branch.

## report

Report the results of the `RUN` commands with a path to the worktree directory, the branch name and the path to each .env Ile copied to the worktree directory
