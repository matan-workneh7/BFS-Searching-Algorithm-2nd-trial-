# Architecture Documentation

## Overview

This project follows clean architecture principles with strict separation of concerns, implementing a professional, maintainable codebase structure.

## 🏗️ Architecture Layers

### 1. Configuration Layer (`src/config/`)
**Responsibility**: Centralized configuration management
- `settings.py`: All application settings, colors, limits, locations
- Single source of truth for configuration
- Environment-specific settings support

### 2. Models Layer (`src/models/`)
**Responsibility**: Data management and basic operations
- `graph_model.py`: Road network graph management
- `location_model.py`: Location lookup and geocoding
- No business logic, only data operations

### 3. Services Layer (`src/services/`)
**Responsibility**: Core business logic implementation
- `pathfinding_service.py`: Algorithm implementations (BFS, DFS, Greedy)
- `visualization_service.py`: Map visualization and plotting
- Complex operations and algorithms

### 4. Controllers Layer (`src/controllers/`)
**Responsibility**: Workflow orchestration and user interaction
- `pathfinding_controller.py`: Main application coordinator
- Dependency injection and component coordination
- User-facing API

### 5. Utils Layer (`src/utils/`)
**Responsibility**: Reusable helper functions
- `path_calculator.py`: Mathematical calculations
- `constraint_validator.py`: Business rule validation
- Stateless, pure functions

## 🔄 Data Flow

```
User Input → Controller → Services → Models → Utils
     ↑              ↓           ↓        ↓       ↓
   Output ← Controller ← Services ← Models ← Utils
```

### Typical Request Flow:
1. **Controller** receives user request
2. **Controller** validates using **Utils**
3. **Controller** calls appropriate **Service**
4. **Service** uses **Models** for data operations
5. **Service** uses **Utils** for calculations
6. **Controller** formats and returns results
7. **Controller** coordinates **Visualization Service** for output

## 📋 Design Principles Applied

### Single Responsibility Principle (SRP)
- Each class has one reason to change
- `GraphModel` only manages graph data
- `PathfindingService` only implements algorithms
- `VisualizationService` only creates visualizations

### Dependency Inversion Principle (DIP)
- High-level modules don't depend on low-level modules
- Both depend on abstractions (interfaces)
- Controller injects dependencies into services

### Open/Closed Principle (OCP)
- Open for extension, closed for modification
- New algorithms can be added without changing existing code
- New visualization styles can be added easily

### Don't Repeat Yourself (DRY)
- Common functionality extracted to utils
- Configuration centralized
- Consistent error handling patterns

## 🗂️ File Organization

### By Purpose/Domains
```
src/
├── config/          # Configuration (settings, constants)
├── controllers/     # User interaction coordination
├── models/         # Data models and basic operations
├── services/       # Business logic and algorithms
└── utils/          # Reusable helper functions
```

### One Responsibility Per File
- `graph_model.py` - Only graph data management
- `path_calculator.py` - Only mathematical calculations
- `constraint_validator.py` - Only validation logic
- No "god files" with multiple responsibilities

## 🔗 Dependencies Management

### Dependency Injection
```python
class PathfindingController:
    def __init__(self):
        self.graph_model = GraphModel()
        self.location_model = LocationModel(self.graph_model.graph)
        self.pathfinding_service = PathfindingService(self.graph_model, self.location_model)
        self.visualization_service = VisualizationService(self.graph_model, self.location_model)
```

### No Circular Dependencies
- Models → Utils (allowed)
- Services → Models, Utils (allowed)
- Controllers → Services, Models, Utils (allowed)
- Utils → Nothing (pure functions)

## 🧪 Testing Strategy

### Unit Tests by Layer
- **Models**: Test data operations
- **Services**: Test business logic
- **Utils**: Test pure functions
- **Controllers**: Test workflow coordination

### Mock Dependencies
- Mock external dependencies (OSMnx, NetworkX)
- Mock file system operations
- Mock user input for controller tests

## 📈 Performance Considerations

### Memory Efficiency
- Parent tracking instead of full path storage: O(V+E) vs O(V²)
- Streaming generators for large result sets
- Lazy loading of graph data

### Algorithm Optimizations
- Single BFS with parent tree vs multiple BFS runs
- Early termination when limits reached
- Intelligent caching of frequently used data

## 🔧 Configuration Management

### Centralized Settings
```python
# All settings in one place
DEFAULT_MAX_PATHS = 5
VISUALIZATION_COLORS = {"primary": "red", ...}
CONSTRAINT_MESSAGES = {"unknown_location": "...", ...}
```

### Environment-Specific Configs
- Different settings for development/production
- Easy to modify without code changes
- Type-safe configuration access

## 🎯 Extensibility

### Adding New Algorithms
1. Implement in `PathfindingService`
2. Add configuration options
3. Update controller interface
4. No changes to models or utils needed

### Adding New Visualizations
1. Extend `VisualizationService`
2. Add color schemes to configuration
3. Update controller calls
4. No algorithm changes needed

### Adding New Constraints
1. Add validation logic to `ConstraintValidator`
2. Add messages to configuration
3. Update service constraint handling
4. Isolated changes only

## 📝 Code Quality Standards

### Naming Conventions
- **Files**: snake_case (`pathfinding_service.py`)
- **Classes**: PascalCase (`PathfindingService`)
- **Functions**: snake_case (`find_optimal_paths`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_MAX_PATHS`)

### Documentation
- Docstrings for all public methods
- Type hints for all function signatures
- Complex logic explanations in comments
- README files for major components

### Error Handling
- Consistent exception patterns
- Graceful degradation for non-critical errors
- User-friendly error messages
- Proper logging for debugging

## 🔄 Future Enhancements

### Web API Layer
- Add `routes/` package for HTTP endpoints
- Separate web controllers from business controllers
- API versioning support

### Database Integration
- Add `repositories/` package for data persistence
- Abstract data access behind interfaces
- Support multiple database backends

### Caching Layer
- Add `cache/` package for caching strategies
- Redis integration for distributed caching
- Cache invalidation strategies

This architecture ensures maintainability, testability, and extensibility while following industry best practices for Python applications.
