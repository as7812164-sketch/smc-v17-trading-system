.class final LN/o$b;
.super LN/h;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = LN/o;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x18
    name = "b"
.end annotation


# instance fields
.field private final transient c:LN/g;

.field private final transient d:LN/f;


# direct methods
.method constructor <init>(LN/g;LN/f;)V
    .locals 0

    .line 1
    invoke-direct {p0}, LN/h;-><init>()V

    .line 2
    .line 3
    .line 4
    iput-object p1, p0, LN/o$b;->c:LN/g;

    .line 5
    .line 6
    iput-object p2, p0, LN/o$b;->d:LN/f;

    .line 7
    .line 8
    return-void
.end method


# virtual methods
.method a([Ljava/lang/Object;I)I
    .locals 1

    .line 1
    invoke-virtual {p0}, LN/o$b;->e()LN/f;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-virtual {v0, p1, p2}, LN/f;->a([Ljava/lang/Object;I)I

    .line 6
    .line 7
    .line 8
    move-result p1

    .line 9
    return p1
.end method

.method public contains(Ljava/lang/Object;)Z
    .locals 1

    .line 1
    iget-object v0, p0, LN/o$b;->c:LN/g;

    .line 2
    .line 3
    invoke-virtual {v0, p1}, LN/g;->get(Ljava/lang/Object;)Ljava/lang/Object;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    if-eqz p1, :cond_0

    .line 8
    .line 9
    const/4 p1, 0x1

    .line 10
    return p1

    .line 11
    :cond_0
    const/4 p1, 0x0

    .line 12
    return p1
.end method

.method public e()LN/f;
    .locals 1

    .line 1
    iget-object v0, p0, LN/o$b;->d:LN/f;

    .line 2
    .line 3
    return-object v0
.end method

.method public i()LN/q;
    .locals 1

    .line 1
    invoke-virtual {p0}, LN/o$b;->e()LN/f;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    invoke-virtual {v0}, LN/f;->g()LN/q;

    .line 6
    .line 7
    .line 8
    move-result-object v0

    .line 9
    return-object v0
.end method

.method public bridge synthetic iterator()Ljava/util/Iterator;
    .locals 1

    .line 1
    invoke-virtual {p0}, LN/o$b;->i()LN/q;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    return-object v0
.end method

.method public size()I
    .locals 1

    .line 1
    iget-object v0, p0, LN/o$b;->c:LN/g;

    .line 2
    .line 3
    invoke-interface {v0}, Ljava/util/Map;->size()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method
