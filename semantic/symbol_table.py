from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    data_type: str
    scope_level: int
    initialized: bool = False


class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_level = 0

    def enter_scope(self):
        self.scopes.append({})
        self.scope_level += 1

    def exit_scope(self):
        if self.scope_level == 0:
            raise RuntimeError("Cannot exit global scope")

        self.scopes.pop()
        self.scope_level -= 1

    def declare(self, name, data_type, initialized=False):
        current_scope = self.scopes[-1]

        if name in current_scope:
            raise RuntimeError(
                f"Variable '{name}' already declared "
                f"in current scope"
            )

        symbol = Symbol(
            name=name,
            data_type=data_type,
            scope_level=self.scope_level,
            initialized=initialized,
        )

        current_scope[name] = symbol

        return symbol

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None

    def lookup_current_scope(self, name):
        return self.scopes[-1].get(name)

    def __str__(self):
        lines = ["Symbol Table", "------------"]

        for level, scope in enumerate(self.scopes):
            lines.append(f"Scope {level}:")

            if not scope:
                lines.append("  <empty>")

            for symbol in scope.values():
                lines.append(
                    f"  {symbol.name}: "
                    f"{symbol.data_type}, "
                    f"initialized={symbol.initialized}"
                )

        return "\n".join(lines)