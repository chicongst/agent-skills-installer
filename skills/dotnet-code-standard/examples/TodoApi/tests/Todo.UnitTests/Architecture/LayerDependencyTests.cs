using System.Reflection;
using Todo.Application.Abstractions;
using Todo.Domain.Todos;
using Todo.Infrastructure;

namespace Todo.UnitTests.Architecture;

public sealed class LayerDependencyTests
{
    private static readonly Assembly Domain = typeof(TodoItem).Assembly;
    private static readonly Assembly Application = typeof(ITodoRepository).Assembly;
    private static readonly Assembly Infrastructure = typeof(StorageOptions).Assembly;

    private static string[] ReferencedNames(Assembly assembly) =>
        [.. assembly.GetReferencedAssemblies().Select(name => name.Name ?? string.Empty)];

    [Fact]
    public void Domain_DependsOnNothingButTheBaseLibrary()
    {
        var references = ReferencedNames(Domain);

        Assert.DoesNotContain(references, name => name.StartsWith("Todo.", StringComparison.Ordinal));
        Assert.DoesNotContain(references, name => name.StartsWith("Microsoft.", StringComparison.Ordinal));
    }

    [Fact]
    public void Application_DoesNotDependOnInfrastructureOrWeb()
    {
        var references = ReferencedNames(Application);

        Assert.DoesNotContain(Infrastructure.GetName().Name, references);
        Assert.DoesNotContain(references, name => name.StartsWith("Microsoft.EntityFrameworkCore", StringComparison.Ordinal));
        Assert.DoesNotContain(references, name => name.StartsWith("Microsoft.AspNetCore", StringComparison.Ordinal));
        Assert.DoesNotContain(references, name => name.StartsWith("Npgsql", StringComparison.Ordinal));
    }

    [Fact]
    public void Infrastructure_DoesNotDependOnWeb()
    {
        Assert.DoesNotContain("Todo.Api", ReferencedNames(Infrastructure));
    }

    [Fact]
    public void Repositories_AreNotPublic()
    {
        var repositories = Infrastructure.GetTypes()
            .Where(type => type.IsClass && type.GetInterfaces().Contains(typeof(ITodoRepository)));

        Assert.All(repositories, repository => Assert.False(repository.IsPublic, $"{repository.Name} should be internal"));
    }

    [Fact]
    public void Handlers_AreSealedAndLiveInAUseCaseFolder()
    {
        var handlers = Application.GetTypes().Where(type => type.Name.EndsWith("Handler", StringComparison.Ordinal));

        Assert.All(handlers, handler =>
        {
            Assert.True(handler.IsSealed, $"{handler.Name} should be sealed");
            Assert.StartsWith("Todo.Application.Todos.", handler.Namespace, StringComparison.Ordinal);
        });
    }
}
