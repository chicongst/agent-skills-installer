using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Todo.Application.Todos.CompleteTodo;
using Todo.Application.Todos.CreateTodo;
using Todo.Application.Todos.DeleteTodo;
using Todo.Application.Todos.GetTodo;
using Todo.Application.Todos.ListTodos;
using Todo.Application.Todos.ReopenTodo;
using Todo.Application.Todos.UpdateTodo;

namespace Todo.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.TryAddSingleton(TimeProvider.System);

        services.AddScoped<CreateTodoHandler>();
        services.AddScoped<GetTodoHandler>();
        services.AddScoped<ListTodosHandler>();
        services.AddScoped<UpdateTodoHandler>();
        services.AddScoped<CompleteTodoHandler>();
        services.AddScoped<ReopenTodoHandler>();
        services.AddScoped<DeleteTodoHandler>();

        return services;
    }
}
