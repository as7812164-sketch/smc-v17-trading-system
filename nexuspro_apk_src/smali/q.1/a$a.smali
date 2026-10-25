.class final Lq/a$a;
.super Ljava/util/AbstractSet;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lq/a;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x10
    name = "a"
.end annotation


# instance fields
.field final synthetic a:Lq/a;


# direct methods
.method constructor <init>(Lq/a;)V
    .locals 0

    .line 1
    iput-object p1, p0, Lq/a$a;->a:Lq/a;

    .line 2
    .line 3
    invoke-direct {p0}, Ljava/util/AbstractSet;-><init>()V

    .line 4
    .line 5
    .line 6
    return-void
.end method


# virtual methods
.method public iterator()Ljava/util/Iterator;
    .locals 2

    .line 1
    new-instance v0, Lq/a$d;

    .line 2
    .line 3
    iget-object v1, p0, Lq/a$a;->a:Lq/a;

    .line 4
    .line 5
    invoke-direct {v0, v1}, Lq/a$d;-><init>(Lq/a;)V

    .line 6
    .line 7
    .line 8
    return-object v0
.end method

.method public size()I
    .locals 1

    .line 1
    iget-object v0, p0, Lq/a$a;->a:Lq/a;

    .line 2
    .line 3
    invoke-virtual {v0}, Lq/i;->size()I

    .line 4
    .line 5
    .line 6
    move-result v0

    .line 7
    return v0
.end method
