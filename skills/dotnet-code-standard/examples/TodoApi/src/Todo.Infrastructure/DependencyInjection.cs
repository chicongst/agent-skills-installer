using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Todo.Application.Abstractions;
using Todo.Infrastructure.Persistence;
using Todo.Infrastructure.Todos;

namespace Todo.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        var storage = StorageOptions.Load(configuration);
        var healthChecks = services.AddHealthChecks();

        if (storage.Driver == StorageDriver.Memory)
        {
            services.AddSingleton<ITodoRepository, InMemoryTodoRepository>();
            return services;
        }

        services.AddDbContext<TodoDbContext>(options => options.UseNpgsql(storage.ConnectionString));
        services.AddScoped<ITodoRepository, PostgresTodoRepository>();
        healthChecks.AddDbContextCheck<TodoDbContext>(tags: [HealthCheckTags.Ready]);

        return services;
    }
}
